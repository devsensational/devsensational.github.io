---
layout: page
title: "Project OnlyOne"
permalink: /portfolio/portfolio_project_onlyone/
---

## 프로젝트 개요
---

{% include embed/youtube.html id='vKjQAP-kGwM' %}

- **프로젝트 명:** Project OnlyOne (Team 16-bit)
- **장르:** AI 군중 속에 숨은 플레이어를 행동으로 찾아내는 Last Man Standing 방식 멀티플레이 게임
- **역할**
    - 팀장 (회의 진행, 코드 리뷰, Git·Notion 관리)
    - 프로젝트 생성 및 초기 세팅
    - 게임 UI 전체 설계 및 구현
    - 서버 로비 및 Listen Server 테스트 환경 구현
    - 코드 병합 관리
- **개발 환경**
    - Unreal 5.5.4
    - C++
    - PC/Windows
- **기간:** 2025.09.08 ~ 2025.10.16
- **인원:** 5명

> 캐릭터, AI 군중, GAS 기반 기믹은 팀원이 담당했으며, 이 페이지에는 본인이 담당한 팀 리딩, UI, 로비·테스트 환경 작업만 담았습니다.

---

## 핵심 기능

### 1. 팀 리딩 및 협업 체계 구축

![노션 기반 협업 관리](/assets/images/old/2216c896-cabf-47ff-9d1a-5d3aaed2cf6d-image.png)

> **팀장으로서 데일리 스크럼, 마일스톤별 KPT 회고, 코드 리뷰 담당제, Git 브랜치 규칙을 도입해 5인 팀이 일정 내에 한 판의 게임 사이클을 완성하도록 이끌었습니다.**

#### 주요 내용

- **협업 프로세스 설계**
    - 매일 데일리 스크럼 진행, 회의록은 녹음 → 텍스트 변환 → AI 요약으로 작성
    - 마일스톤(M1, M2, 최종)마다 KPT(Keep / Problem / Try) 회고를 진행하고, 도출한 Try 항목을 다음 마일스톤에 반영
    - Notion 칸반보드로 작업 현황을 공유하고, Slack으로 이슈를 실시간 공유

    ![칸반 보드](/assets/images/old/eb87e0c4-9334-4066-a9bc-a03316fad4a8-image.png)

- **코드 품질 및 병합 관리**
    - 코드 컨벤션과 GitHub 브랜치 규칙을 정하고, 브랜치를 작업 단위로 세분화하도록 유도
    - PR마다 리뷰 담당자를 지정해 "누군가 하겠지" 식의 리뷰 공백을 없애고, 병합을 직접 관리

    → 회고에서 브랜치 세분화로 **merge 시 conflict가 크게 줄었다**는 평가

    ![코드 컨벤션 및 GitHub Rule](/assets/images/old/702fd525-a6a1-4dac-935a-fb7df67909cc-image.png)

- **프로젝트 초기 세팅**
    - 프로젝트 생성, 폴더 구조 설계, 모듈 시작 시 Native GameplayTags 초기화
    - 멀티플레이 디버깅을 위해 **NetMode(Server/Client 번호)와 Local/Remote Role, 호출 함수명을 함께 출력하는 로그 매크로(`LOG_NET`) 제작**

    ```cpp
    #define LOG_NET(LogCat, Verbosity, Format, ...) UE_LOG(LogCat, Verbosity, TEXT("[%s][%s/%s] %s %s"), \
        LOG_NETMODEINFO, LOG_LOCALROLEINFO, LOG_REMOTEROLEINFO, LOG_CALLINFO, *FString::Printf(Format, ##__VA_ARGS__))
    ```

#### 핵심 기여

- 데일리 스크럼·KPT 회고 기반 팀 운영
- 코드 컨벤션, 브랜치 규칙, 리뷰 담당제 도입 및 병합 관리
- 멀티플레이용 네트워크 로그 매크로 등 프로젝트 초기 환경 구축

#### 구현 과정

[[Project OnlyOne] 프로젝트 시작]({% post_url 2025-09-08-[Project OnlyOne] 프로젝트 시작 %})

[[Project OnlyOne] 프로젝트 기획 및 역할 할당]({% post_url 2025-09-09-[Project OnlyOne] 프로젝트 기획 및 역할 할당 %})

[[Project OnlyOne] Milestone 1 평가 및 회고, Main Merge]({% post_url 2025-09-19-[Project OnlyOne] Milestone 1 평가 및 회고, Main Merge %})

[[Project OnlyOne] Milestone 2 평가 및 회고]({% post_url 2025-10-01-[Project OnlyOne] Milestone 2 평가 및 회고 %})

### 2. 스택 기반 UI 관리 구조와 재사용 위젯

![UI Stacking](/assets/images/old/19f3ae07-2c4f-440e-b5b5-65d73d9accad-image.webp)

> **PlayerController가 소유한 UI 관리 컴포넌트로 팝업·모달의 수명, 입력 모드, 가시성을 Push/Pop 두 API로 통합하고, 버튼·창 위젯을 재사용 가능한 클래스로 만들어 중복 제작을 없앴습니다.**

#### 기술적 포인트

- **스택(LIFO) 기반 UI 관리 (`UPOUIStackingComponent`)**
    - `PushWidget`: 기존 최상단 위젯을 `Collapsed`로 접고 새 위젯을 `AddToViewport` 후 `Visible`로 표시
    - `PopWidget`: 최상단 위젯을 `RemoveFromParent` 후 직전 위젯을 `Visible`로 복원
    - 스택이 비어 있다가 처음 Push될 때 `FInputModeUIOnly` + 마우스 커서 On, 스택이 비면 게임 입력으로 복귀
    - index 0을 항상 남는 **Default Widget(베이스 HUD)** 자리로 예약하고, Pop 가드(`Num <= 1`)로 HUD가 제거되지 않도록 처리
    - 하위 위젯을 `Collapsed`로 두어 렌더·히트테스트·레이아웃 비용 절감

    → 새 팝업은 `PushWidget` 호출만으로 추가

- **재사용 버튼 클래스 (`UPOCustomButton`)**
    - UMG에서 위젯 하나에 애니메이션을 하나만 지정할 수 있어, 버튼이 늘 때마다 같은 애니메이션을 반복 제작해야 하는 문제 발견
    - 애니메이션과 텍스트를 가진 버튼 클래스를 만들고, 클릭 시 자기 자신을 넘기는 Dynamic Multicast Delegate(`OnCustomButtonClicked`)로 이벤트 전달

    ![메인 메뉴](/assets/images/old/7a4e16e3-853e-4e5a-ba71-68776e800e0c-image.webp)

- **공용 Window 위젯 (`UPOBaseWindow`)**
    - Join Server, 설정, 알림창 등에서 반복되는 창 형식(테두리 + 닫기 버튼)을 공용 위젯으로 분리
    - 닫기 버튼이 창 테두리만 숨기고 내용은 남는 문제를 **닫기 Delegate**로 해결: 창은 `OnCloseWindow`를 Broadcast만 하고, 내용 위젯이 `BindWidget`으로 창을 참조해 닫기 동작을 직접 결정

    ![Join Server UI](/assets/images/old/9de71e69-9291-4b73-8ef8-ea439a3a1a75-image.png)

#### 핵심 기여

- 스택 기반 UI 관리 컴포넌트 설계 및 구현 (수명·입력 모드·가시성 통합 관리)
- Delegate 기반 재사용 버튼·창 위젯 구조 설계

#### 구현 과정

[[Project OnlyOne] Main UI 프로토타입 구현]({% post_url 2025-09-10-[Project OnlyOne] Main UI 프로토타입 구현 %})

[[Project OnlyOne] 공용 Window UI, Join Server UI 구현 + 다중 바인딩 문제 해결]({% post_url 2025-09-11-[Project OnlyOne] 공용 Window UI, Join Server UI 구현 + 다중 바인딩 문제 해결 %})

[[Project OnlyOne] 복수의 UI 관리를 위한 UI Stacking 구현]({% post_url 2025-09-17-[Project OnlyOne] 복수의 UI 관리를 위한 UI Stacking 구현 %})

### 3. 인게임 UI (HUD, 킬 피드, 플레이어 상태 목록, 타이머)

![HUD](/assets/images/old/90498b9b-d069-416b-9644-123f7013d77d-image.png)

> **남은 플레이어 수, 시간, 스킬 잔여 횟수를 담은 HUD부터 킬 피드, 플레이어 상태 목록, 타이머, 설정, 승리 결과까지 게임 한 판의 흐름을 안내하는 UI를 구현했습니다.**

#### 기술적 포인트

- **Kill Feed (`UPOKillFeedWidget` / `UPOKillFeedElementWidget`)**
    - 컨테이너 위젯이 ScrollBox에 항목 위젯을 동적으로 추가하고, `KillFeedDuration` 타이머가 끝나면 제거
    - 항목 위젯은 텍스트 표시만 담당하고 Viewport 추가·제거는 컨테이너가 관리하도록 책임 분리
    - `NativeDestruct`에서 등록된 타이머를 모두 정리해 위젯 파괴 후 콜백 실행 방지

    ![Kill Feed](/assets/images/old/cf23d8ab-f264-41e9-8ab7-18ceac18497c-image.webp)

- **Player State List (Tab 키 생존·킬 현황)**
    - PlayerController의 Multicast Delegate(`OnSetPlayerStateEntry`)를 목록 위젯이 구독해 게임 로직과 UI를 느슨하게 결합
    - `TMap<FString, Element>`로 닉네임 키 기반 중복 생성 방지, 항목 위젯은 생성 전에 들어온 값을 캐싱했다가 `NativeConstruct`에서 적용
    - 위젯 생성 전·숨김 상태에서 들어온 이벤트 유실 문제를 `TQueue` 지연 적용으로 해결 (트러블 슈팅 1번 참조)

    ![Player State List](/assets/images/old/b5f5337b-09db-4a3e-9e8c-55ab9daa8a9c-image.webp)

- **Stage Timer**
    - `NativeConstruct`에서 GameState를 캐싱해 초기값을 즉시 표시한 뒤, `OnStageTimeUpdated` Delegate로 매초 갱신
    - 음수 시간을 0으로 클램프하고 `MM:SS` 형식으로 변환, `NativeDestruct`에서 Delegate 해제

    ![Stage Timer](/assets/images/old/552f42f7-b1f3-474f-9a90-d7d98320b911-image.webp)

- **게임 흐름 UI 통합**
    - 설정(민감도·음량), 준비 시간 도움말, 상호작용 키 안내 및 외곽선 표시, 승리 결과 후 로비 복귀 UI 구현

| 설정 | 준비 시간 |
| --- | --- |
| ![설정 UI](/assets/images/old/05efb602-4f9d-43de-a656-0fad844f79f4-image.png) | ![준비 시간 UI](/assets/images/old/02cacc3d-0d6a-432f-8301-47d0d8b0c328-image.png) |

| 상호작용 | 승리 결과 |
| --- | --- |
| ![상호작용 UI](/assets/images/old/af813ae6-32e0-4fd2-8f0f-a245d6c9b254-image.png) | ![승리 결과](/assets/images/old/eceeabba-5cc9-47bb-a545-79443ebacc5f-image.png) |

#### 핵심 기여

- HUD, 킬 피드, 플레이어 상태 목록, 타이머, 설정, 승리 결과 등 게임 UI 전체 구현
- Delegate 기반 게임 로직 ↔ UI 느슨한 결합 구조 적용
- 위젯 생명주기(`NativeConstruct` / `NativeDestruct`)에 맞춘 바인딩·타이머 정리

#### 구현 과정

[[Project OnlyOne] Player 상태 정보를 나타내는 리스트 UI]({% post_url 2025-09-24-[Project OnlyOne] Player 상태 정보를 나타내는 리스트 UI %})

[[Project OnlyOne] Kill Feed]({% post_url 2025-09-25-[Project OnlyOne] Kill Feed %})

[[Project OnlyOne] Stage Timer와 UI Stacking 업데이트]({% post_url 2025-09-26-[Project OnlyOne] Stage Timer와 UI Stacking 업데이트 %})

[[Project OnlyOne] UI 퀄리티 향상 및 통합 작업]({% post_url 2025-10-13-[Project OnlyOne] UI 퀄리티 향상 및 통합 작업 %})

### 4. 서버 로비 및 Listen Server 테스트 환경

![Server Lobby](/assets/images/old/4c37f019-61b9-4667-bd3b-07c25fe050ac-image.webp)

> **IP와 닉네임으로 서버에 접속해 다른 플레이어와 대기하고 준비 상태를 동기화하는 로비를 구현했으며, 테스트마다 패키징이 필요하던 문제를 Listen Server 호스팅 기능으로 해결했습니다.**

#### 기술적 포인트

- **서버 로비 시스템**
    - 구조: `POMainMenuPlayerController` → (접속) → `POServerLobbyPlayerController` ↔ `POLobbyPlayerState` / `POLobbyGameState` / `POServerLobbyWidget`
    - IP 주소와 닉네임을 입력해 접속하고, 접속 중인 플레이어 목록을 실시간 표시
    - 플레이어별 Ready 상태 토글 및 동기화, 입장·퇴장 시 UI 즉시 갱신

    ![로비 실행 Sequence](/assets/images/old/d4649dc3-e8a2-4d11-bc5a-1deaa8c3bd38-image.png)

- **플레이어 슬롯 동적 관리**
    - `TMap<FString, TObjectPtr<UPOServerLobbyPlayerElementWidget>>`으로 플레이어 이름을 키로 슬롯을 관리해 중복 생성 방지
    - 입장 시 `CreateWidget`으로 슬롯을 만들어 ScrollBox에 추가, 퇴장 시 `RemoveFromParent`와 맵 제거를 함께 수행해 UI와 데이터 일관성 유지
    - 테스트 버튼으로 가상 플레이어 입장·퇴장을 재현해 네트워크 없이 UI 동작 검증

    ![로비 UI 테스트](/assets/images/old/ee54d131-72b4-46bf-b24d-6da5a33af588-image.webp)

- **Listen Server 기반 테스트 환경**
    - Dedicated Server 대상 프로젝트라 테스트할 때마다 패키징이 필요했고, 자동 패키징 환경이 없어 생산성 저하
    - 메인 메뉴에 Host Server 버튼과 `POHostServerWidget`(닉네임 입력)을 추가하고, `OpenLevel`의 `listen` 옵션으로 로비 레벨을 직접 호스팅
    - 사용자 정보는 GameInstance에 저장해 레벨 이동 후에도 유지

    → **에디터에서 바로 멀티플레이 테스트 가능**

    ![Listen Server](/assets/images/old/f212b4f4-f6d6-4fbf-81a6-4f0fea582564-image.webp)

#### 핵심 기여

- 서버 접속, 플레이어 입퇴장 표시, 준비 상태 동기화 로비 구현
- Listen Server 호스팅 기능으로 패키징 없는 테스트 환경 구축

#### 구현 과정

[[Project OnlyOne] Server Lobby UI 구현]({% post_url 2025-09-12-[Project OnlyOne] Server Lobby UI 구현 %})

[[Project OnlyOne] Server Lobby와 Client-Server 동기화 및 문제 해결]({% post_url 2025-09-14-[Project OnlyOne] Server Lobby와 Client-Server 동기화 및 문제 해결 %})

[[Project OnlyOne] Listen Server를 활용한 테스트 환경 구축]({% post_url 2025-09-15-[Project OnlyOne] Listen Server를 활용한 테스트 환경 구축 %})

---

## 트러블 슈팅

### 1. 위젯 초기화 전·숨김 상태에서 발생한 PlayerState 이벤트 유실 문제 해결

#### 문제 상황
- Tab 키로 여는 플레이어 상태 목록에 일부 플레이어의 생존 상태와 킬 수가 반영되지 않음

#### 원인 분석
- 처음에는 PlayerController 생성 시점에 위젯을 만들면 해결될 것으로 보고 시도했으나 해결되지 않음
- 시행착오 끝에 **PlayerState가 게임 시작 전 Lobby에서 이미 생성되고, ServerTravel 이후에도 유지되어 다시 초기화되지 않는다**는 점을 확인
- 그 결과 상태 변경 이벤트가 위젯보다 먼저 도착하거나, 위젯이 숨겨진 동안 도착해 아래 세 경우에 유실됨

| 문제         | 설명                                       | 결과적 위험                          |
| ------------ | ------------------------------------------ | ------------------------------------ |
| 위젯 미생성  | 아직 `CreateWidget` 호출 전                | 이벤트 무시/유실                     |
| Slate 미구성 | `CreateWidget` 후 `AddToViewport` 이전     | 바인딩 위젯 접근·갱신 불안정         |
| 비가시 상태  | Collapsed / Hidden 상태에서 이벤트 발생    | 표시 순간 UI와 실제 게임 상태 불일치 |

#### 해결 방법
**1. 컨트롤러에서 이벤트를 먼저 수신**
- PlayerController가 이른 시점부터 `OnSetPlayerStateEntry`를 구독해 위젯 상태와 관계없이 이벤트를 수신

**2. `TQueue` 기반 지연 적용**
- 위젯이 Viewport에 있고 `Visible`이면 즉시 반영, 그렇지 않으면 `PlayerStateQueue`에 저장
- 목록을 표시하는 `ShowListWidget()`에서 위젯 생성을 보장한 뒤 Queue를 순서대로(FIFO) 비우며 반영

#### 결과
- 위젯 생성·표시 시점과 네트워크 이벤트 도착 시점을 분리해 **이벤트 손실 없이 표시 시점의 상태 일관성 확보**
- 한계: 같은 플레이어의 변화가 모두 재생되므로, 최신 상태만 필요하다면 닉네임 키 기반 스냅샷 방식이 더 효율적이라는 개선점 정리

#### 해결 과정

[[Project OnlyOne] Player State List UI의 동기화 문제 해결]({% post_url 2025-09-29-[Project OnlyOne] Player State List UI의 동기화 문제 해결 %})

### 2. Client에서만 준비 시간 UI가 표시되지 않는 문제 해결

![준비 시간 UI 문제](/assets/images/old/91597b7d-fce9-4091-a884-463f6e8d9eaa-image.png)

#### 문제 상황
- 준비(Prep) 단계에서 Host에는 준비 시간 UI가 정상 출력되지만 Client에는 출력되지 않음

#### 원인 분석
- 게임 단계(`EPOStagePhase`)가 None → Prep → Main으로 바뀔 때 Delegate로 UI를 켜고 끄는 구조
- Host는 Prep으로 바뀔 때 PlayerController가 이미 있었지만, **Client는 PlayerController가 생성되기 전에 Prep으로 바뀌어** UI를 켜는 이벤트를 받지 못함

#### 해결 방법
- 준비 시간 UI는 게임 시작 직후 반드시 필요한 UI이므로, 단계 변경 이벤트 대신 **PlayerController `BeginPlay`에서 `IsLocalController()`일 때 바로 표시**
- 단계 변경 Delegate는 Prep이 아닌 단계로 바뀔 때 UI를 숨기는 용도로만 사용
- 남은 시간은 서버에서 매초 Replicate되므로 별도 수정 없이 동기화

#### 결과
- Host와 Client 모두 준비 시간 UI가 정상 출력

#### 해결 과정

[[Project OnlyOne] Prep 단계 UI 동기화 문제 해결]({% post_url 2025-10-14-[Project OnlyOne] Prep 단계 UI 동기화 문제 해결 %})

### 3. 위젯 재표시 시 Delegate 다중 바인딩 문제 해결

#### 문제 상황
- Join Server 버튼을 누를 때마다 같은 처리가 여러 번 실행됨

#### 원인 분석
- 버튼을 누를 때마다 `AddToViewport()`를 호출했고, 그때마다 Delegate 바인딩이 들어 있는 `NativeConstruct()`가 다시 호출되어 같은 함수가 중복 바인딩됨

#### 해결 방법
- 위젯은 **처음 생성할 때만 `AddToViewport()`**하고, 이후에는 `SetVisibility()`로 표시 상태만 전환
- 바인딩 전에 `IsBound()`를 확인하고, 위젯 파괴 시 바인딩된 Delegate를 정리

#### 결과
- 팝업을 반복해서 열고 닫아도 이벤트가 1회만 실행되는 안정적인 UI 구조 확보

#### 해결 과정

[[Project OnlyOne] 공용 Window UI, Join Server UI 구현 + 다중 바인딩 문제 해결]({% post_url 2025-09-11-[Project OnlyOne] 공용 Window UI, Join Server UI 구현 + 다중 바인딩 문제 해결 %})

### 4. 플레이어 퇴장이 로비 UI에 즉시 반영되지 않는 문제 해결

#### 문제 상황
- 플레이어가 서버를 나가도 로비 목록에서 바로 사라지지 않음

#### 원인 분석
- PlayerState의 `BeginDestroy`에서 퇴장 처리를 호출했으나, `BeginDestroy`는 퇴장 직후가 아니라 **GC가 실행될 때 호출**되어 반영 시점을 보장할 수 없음

#### 해결 방법
- 서버의 `GameMode::Logout`에서 퇴장하는 PlayerState의 **Multicast RPC**(`MulticastPlayerLeftLobby`)를 호출
- 각 클라이언트는 RPC를 받아 로컬 PlayerController의 `OnPlayerLeaveLobby` Delegate를 Broadcast해 로비 UI에서 해당 슬롯 제거

#### 결과
- 퇴장 즉시 모든 접속자의 로비 목록에 반영

#### 해결 과정

[[Project OnlyOne] Server Lobby와 Client-Server 동기화 및 문제 해결]({% post_url 2025-09-14-[Project OnlyOne] Server Lobby와 Client-Server 동기화 및 문제 해결 %})

---

## 결과 및 회고

- 로비 접속부터 게임 진행, 승리 결과, 로비 복귀까지 **한 판의 게임 사이클이 동작하는 빌드 완성** 및 시연 영상 제작
- 최종 KPT 회고에서 팀원들로부터 "팀장으로서 책임감 있는 코드 리뷰와 방향성 제시로 프로젝트 품질 향상에 기여했다"는 평가
- **아쉬운 점과 이후 개선**
    - 로비 입장 시 기존 플레이어 정보 초기화는 1초 타이머 지연으로 임시 해결해, 네트워크 지연이 더 크면 보장되지 않는 한계가 있었음
    - 다음 프로젝트인 [Project Arc](/portfolio/portfolio_project_arc/)에서는 같은 유형의 문제를 **다음 Tick 재시도와 가드 플래그**로 해결해, 고정 지연 없이 동기화를 보장하도록 개선
    - 초기 역할 분배가 모호해 다른 팀원의 작업물을 수정하는 일이 있었고, 회고를 통해 작업 단위를 더 잘게 나누고 담당자 표기와 브랜치 네이밍을 통일하는 방향을 정리

#### 회고 원문

[[Project OnlyOne] 프로젝트 마무리 및 회고]({% post_url 2025-10-21-[Project OnlyOne] 프로젝트 마무리 및 회고 %})

<br><br>

<div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
  <a href="/portfolio/" style="display: inline-block; padding: 14px 28px; font-size: 1.05rem; font-weight: 600; color: #495057; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 8px; text-decoration: none; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease-in-out;">
    <i class="fas fa-arrow-left" style="margin-right: 8px; color: #6c757d;"></i> 포트폴리오 리스트로 돌아가기
  </a>
</div>
