---
title: "[Project Arc] Steam Online Service를 이용한 세션 생성 및 참여 구현 과정 (v5.6.1)"
description: "Steam Online Subsystem을 사용해 친구 초대 및 멀티플레이 기능을 구현하던 중, 세션 생성과 참가(JoinSession)는 정상적으로 콜백이 오는데 실제로는 접속이 되지 않는 문제가 발생하였습니다."
date: 2025-11-28T05:23:48.310Z
tags: ["Project ARC","UE5"]
thumbnail: /assets/images/old/e9e53c93-23a5-409c-ba62-4c341aab70eb-image.png
categories: [Project CM + Project Arc]
---
Steam Online Subsystem을 사용해 친구 초대 및 멀티플레이 기능을 구현하던 중, 세션 생성과 참가(JoinSession)는 정상적으로 콜백이 오는데 실제로는 접속이 되지 않는 문제가 발생하였습니다. 특히 `NetworkDriver` 생성 실패, `Listen` 서버 생성 실패, P2P 연결 타임아웃 등 다양한 로그 메시지가 출력되면서 원인을 추적하는 데 많은 시간이 걸렸습니다.

이 글에서는 문제를 해결하기까지의 시행착오 과정을 정리하여, 비슷한 이슈를 겪는 분들께 참고가 될 만한 내용을 공유드리고자 합니다.

---
### 1.1 문제 상황 요약
- Steam 초대 수락 후 `JoinSession` 까지는 성공 로그가 뜸
- 하지만 실제로는 호스트에 접속되지 않고, 일정 시간이 지난 후 타임아웃
- 클라이언트 로그 상 주요 현상:
  - `OnSessionUserInviteAccepted` 성공
  - `JoinSession` 성공
  - `Browse: steam.7656.../Game/Maps/MainMenu` 까지 진행
  - 이후 `Your connection to the host has been lost.` 로 실패

### 1.2 최초 에러: NetworkDriver 생성 실패
![](/assets/images/old/e9e53c93-23a5-409c-ba62-4c341aab70eb-image.png)

- 로그 예시

>
```
Failed to find object 'Class /Script/Engine.IpNetDriver'
CreateNamedNetDriver failed to create driver from definition GameNetDriver
Error initializing the pending net driver. Check the configuration of NetDriverDefinitions...
```
  

- 원인 추정
  - `DefaultEngine.ini` 에서 `GameNetDriver` 설정이 제대로 되어 있지 않아서, 엔진이 `NetDriver` 클래스를 찾지 못함

#### 1.2.1 NetDriver 설정 수정
![](/assets/images/old/5ec188c6-da20-4227-ba76-adc479dbdc6e-image.png)

- `DefaultEngine.ini` 에 다음과 같이 설정
  - `[/Script/Engine.GameEngine]`
  - `!NetDriverDefinitions=ClearArray`
  - `NetDriverDefinitions=(DefName="GameNetDriver",DriverClassName="/Script/OnlineSubsystemSteam.SteamNetDriver",DriverClassNameFallback="/Script/OnlineSubsystemUtils.IpNetDriver")`
- 효과
  - 이후 로그에서 `InitBase PendingNetDriver (NetDriverDefinition GameNetDriver)` 로 정상 초기화되는 것을 확인
  - 더 이상 `IpNetDriver` 클래스를 못 찾는 에러는 발생하지 않음

### 1.3 두 번째 문제: P2P 연결 타임아웃

![](/assets/images/old/74ad18f6-834a-446a-a7e0-99125c9b0c6e-image.png)

- 수정 후 클라이언트 로그
  - `InitBase PendingNetDriver (NetDriverDefinition GameNetDriver)`
  - `Game client on port 7777, rate 100000`
  - 잠시 대기 후
  - `Timed out attempting to connect`
  - `Your connection to the host has been lost.`
- 특징
  - 세션 검색, 초대, JoinSession 까지는 모두 정상 동작
  - 실제 P2P 연결 수립 단계에서 일정 시간 후 타임아웃 발생

### 1.4 Listen 서버 생성 실패 로그 분석
- 호스트 쪽 로그에서 다음 메시지 확인
  - `LoadMap: failed to Listen(/Game/MainStage/L_GenerateMapTest?Name=Player?listen)`
- 다른 시점에는
  - `LoadMap: failed to Listen(/Game/Maps/MainMenu?Name=Player?listen)`
- 의미
  - 호스트가 맵을 로드하면서 `?listen` 옵션으로 Listen 서버를 열려고 시도했으나 실패
  - 즉, 클라이언트 문제 이전에 **호스트가 제대로 Listen 서버를 띄우지 못함**

#### 1.4.1 세션 생성과 Travel 순서
- 초기 구현
  - `OnCreateSessionComplete()` 안에서 바로 `ServerTravel` + `?listen` 수행
  - 또는 세션 생성 직후 약간의 딜레이를 준 뒤 `ServerTravel` 호출
- 문제점
  - 세션 생성 직후 엔진/Steam 쪽 초기화가 완전히 끝나지 않은 상태에서 `ServerTravel` 을 수행하면 Listen 서버 생성이 실패할 수 있음
  - 다만 이 경우에는 궁극적인 원인은 아니었음 (딜레이를 줘도 근본 문제가 남아 있었음)

#### 1.4.2 기능 분리
- 조치 사항
  - "Online Session 생성" 과 "ServerTravel(맵 이동 + ?listen)" 을 별도의 함수로 분리
  - 세션 생성 성공 콜백에서는 세션 관련 처리만 담당
  - 맵 이동은 명시적으로 별도 타이밍에 호출하도록 구조 개선
- 의도
  - 디버깅 편의성 향상
  - 세션/네트 워킹 문제와 레벨 로딩/게임 로직을 명확하게 분리

### 1.5 게임 타겟 vs 클라이언트 타겟
- 핵심 원인
  - 프로젝트를 **Client 타겟(CrimsonMoonClient)** 으로 빌드하고 실행하고 있었음
  - Client 타겟은 기본적으로 **Listen 서버를 열 수 없는 구성**
- 결과적으로
  - 호스트를 Client 타겟 실행 파일로 실행 → `?listen` 으로 서버를 열려고 해도 계속 실패
  - 따라서 클라이언트 입장에서는 P2P 연결을 시도하나, 실제로는 열려 있는 Listen 서버가 없어서 결국 타임아웃 발생

#### 1.5.1 해결책: Game 타겟으로 빌드
- 빌드 대상 변경
  - 기존: `CrimsonMoonClient.Target.cs` 기반 빌드 (클라이언트 전용)
  - 변경: `CrimsonMoon.Target.cs` 기반 **Game 타겟** 빌드
- 변경 후 현상
  - 호스트가 `?listen` 으로 정상적으로 Listen 서버를 생성
  - 클라이언트에서 Steam 초대 수락 → `JoinSession` → `Browse steam.xxx/Map` → 정상 접속
  - 실제로 친구 초대 후 함께 플레이 가능한 상태 확인
  
  ![](/assets/images/old/fd1d43a9-9e69-4399-a009-13b36db6a29f-image.png)


### 1.6 정리: 왜 Client 타겟으로는 안 되었는가
- Client 타겟의 특징 (언리얼 빌드 관점 가정)
  - 전용 클라이언트 실행용, 서버 관련 일부 기능이 비활성화/제한될 수 있음
  - Listen 서버(클라이언트 + 서버 겸용)를 여는 패턴에는 적합하지 않음
- Listen 서버 패턴
  - 한 플레이어가 **호스트이자 클라이언트** 역할을 하면서 `?listen` 으로 서버를 열고, 나머지는 그 호스트에 접속하는 구조
  - 이 패턴은 Game 타겟(또는 Editor)에서 실행해야 정상 동작

---

## 2. 배운 점 정리 (TIL)

### 2.1 Steam + UE5 멀티플레이 기본 흐름
- 세션 생성
  - Steam Online Subsystem 이용
  - `CreateSession` → `OnCreateSessionComplete` 콜백 확인
- 호스트 측 레벨 이동
  - Listen 서버를 사용할 경우: `/Game/Map/YourMap?listen` 으로 `ServerTravel`
- 클라이언트 초대 및 Join
  - Steam 초대 → `OnSessionUserInviteAccepted` 콜백
  - `JoinSession` 호출, 성공 시 `GetResolvedConnectString` 으로 주소 획득
  - `ClientTravel` 로 `steam.XXX/Map` 주소로 이동

### 2.2 설정/코드 레벨에서의 체크리스트
- `DefaultEngine.ini`
  - `[/Script/Engine.GameEngine]`
  - `!NetDriverDefinitions=ClearArray`
  - `NetDriverDefinitions=(DefName="GameNetDriver", DriverClassName="/Script/OnlineSubsystemSteam.SteamNetDriver", DriverClassNameFallback="/Script/OnlineSubsystemUtils.IpNetDriver")`
- 세션 생성과 맵 이동 분리
  - 세션 생성 전용 함수
  - Listen 서버용 `ServerTravel` 전용 함수
- Host 빌드 타겟
  - **반드시 Game 타겟(CrimsonMoon.exe)** 로 빌드/실행
  - Client 전용 타겟(CrimsonMoonClient.exe)으로는 Listen 서버를 열 수 없음

### 2.3 로그를 볼 때 집중해서 봐야 하는 포인트
- NetDriver 관련
  - `CreateNamedNetDriver failed to create driver from definition GameNetDriver`
  - `Failed to find object 'Class /Script/Engine.IpNetDriver'`
- Listen 서버 관련
  - `LoadMap: failed to Listen( ... ?listen)`
- 연결 실패 관련
  - `Timed out attempting to connect`
  - `Your connection to the host has been lost.`
- Steam Sockets 관련 경고
  - `Relay candidates enabled by P2P_Transport_ICE_Enable, but P2P_TURN_ServerList is empty`
  - 단순 경고일 수 있으며, 치명적인 에러는 아닐 수 있음 → 진짜 실패 원인은 NetDriver/Listen 쪽에 있을 가능성이 높음

### 2.4 앞으로 비슷한 기능을 구현할 때 주의할 점
- 먼저 **호스트가 제대로 Listen 서버를 뜨는지** 단독 실행으로 확인
- 클라이언트/게임 타겟, 서버 타겟 빌드 설정을 명확하게 구분
- Online Subsystem 설정(`DefaultEngine.ini`) 과 NetDriver 설정을 초기 단계에서 정확히 맞춰둘 것
- 세션 로직과 게임 레벨 로딩/게임플레이 초기화 로직을 분리해서 디버깅 가능하게 설계

---

## 결론
이번 구현의 핵심은 코드나 Steam API 사용법 자체의 문제라기보다는, **빌드 타겟 선택(Game vs Client)** 과 **엔진 설정(NetDriver, Listen 서버 가능 여부)** 이었습니다. 언리얼 멀티플레이를 Steam과 연동해서 구현할 때는, 에디터에서 잘 되던 것이 패키징 후 동작하지 않을 수 있으므로, 어떤 타겟으로 빌드하고 실행하는지부터 확실히 인지하는 것이 중요하다는 점을 다시 한 번 느꼈습니다.

이 TIL이 이후에 비슷한 문제를 겪을 때 빠르게 원인을 좁히는 데 도움이 되기를 바랍니다.

