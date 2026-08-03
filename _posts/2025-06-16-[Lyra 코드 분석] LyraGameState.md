---
title: "[Lyra 코드 분석] LyraGameState"
description: "LyraGameState를 알아보고, 클라이언트에서 게임을 초기화하는 흐름을 알아보겠습니다."
date: 2025-06-16T11:46:58.104Z
tags: ["UE5","코드분석"]
thumbnail: /assets/images/old/06e84640-dfbc-4113-8e14-38ba1a8c7557-image.png
---
저번 글에서는 Experience가 무슨 개념인지, 서버에서 게임을 초기화하는 과정이 어떻게 흘러가는지 알아보았습니다. 이번에는 LyraGameState를 알아보고, 클라이언트에서 게임을 초기화하는 흐름을 알아보겠습니다.

# 먼저, GameState란?
GameState란 Unreal에서 제공하는 클래스로써, 게임의 공용 상태 정보를 서버가 클라이언트에게 복제(Replicate)하기 위해 만들어진 클래스입니다. 즉, GameState의 원본은 서버가 가지고 있고, 이를 복제하여 클라이언트에게 전송한다고 이해하시면 되겠습니다. 보통 게임 중 모든 클라이언트가 공유해야 하는 정보들을 여기에 담습니다. 아래 표는 GameState에 담는 기능들의 예시입니다.


| 기능          | 설명                                         |
| ----------- | ------------------------------------------ |
| 게임의 진행 상태   | 예: 진행 중인지, 게임이 끝났는지 등                      |
| 플레이어 리스트    | 클라이언트에서 접근 가능한 플레이어 상태 목록 (`APlayerState`) |
| 타이머 정보      | 예: 라운드 시간, 카운트다운                           |
| 복제된 데이터 저장소 | 클라이언트에서 UI 표시 등에 쓰일 중요한 데이터들               |

# LyraGameState VS 일반 Unreal GameState
그렇다면 Lyra에서 작성된 GameState는 일반적인 Unreal GameState와 어떤 점이 다를까요? 사실 LyraGameState도 GameState를 상속받아 작성했기 때문에 큰 차이점은 없습니다. 
```
AActor
└── AGameStateBase
    └── AModularGameStateBase (플러그인)
        └── ALyraGameState
        
   ```
   
하지만 저번 글에서 말씀드렸던 Expreience를 서버로 부터 받아와야 한다는 점과, 유연한 구조를 설계하기 위해 여러 기능들이 추가되었습니다. 굳이 비교할 필요는 없지만 비교하면서 구성을 알아보면 좋을 것 같아서 표를 첨부했습니다.

| 항목             | 기본 GameState | LyraGameState                               |
| -------------- | ------------ | ------------------------------------------- |
| 기본 목적          | 게임의 공용 상태 복제 | 공용 상태 + 시스템 상태 확장                           |
| 팀 정보           | 별도 처리 필요     | `LyraTeamAgentInterface` 내장                 |
| 경험치 시스템        | 없음           | `ExperienceManagerComponent`로 경험치/설정 구성     |
| 모듈성            | 일반적인 클래스     | `ModularGameStateBase` 기반으로 플러그인 유연하게 사용 가능 |
| Ability System | 직접 구성 필요     | GAS 연동 구조 내장 (ASC 등록/초기화)                   |

# 주요 특징
## 핵심 컴포넌트
### 1. LyraExperienceManagerComponent
- **역할**: 게임 경험(Experience) 시스템 관리
- **기능**:
  - 게임 모드, 맵, 규칙 등을 정의하는 Experience 로딩
  - Game Feature Plugin 활성화/비활성화
  - Experience 로딩 상태 관리 (Unloaded → Loading → Loaded)
  - 네트워크 복제를 통한 클라이언트 동기화

### 2. LyraAbilitySystemComponent
- **역할**: 게임 전체에 영향을 미치는 어빌리티 시스템 관리
- **기능**:
  - 게임플레이 어빌리티 및 이펙트 관리
  - 게임플레이 큐(Gameplay Cues) 처리
  - 네트워크 복제 모드: Mixed (일부는 서버만, 일부는 모든 클라이언트)
  - IAbilitySystemInterface 구현

## 주요 기능
### 1. 초기화 흐름

```
생성자 → PreInitializeComponents → PostInitializeComponents → BeginPlay → Tick
```

1. **생성자 (Constructor)**:
   - Tick 활성화
   - AbilitySystemComponent 생성 및 복제 설정
   - ExperienceManagerComponent 생성
   - ServerFPS 초기화
   
2. **PreInitializeComponents**:
   - 부모 클래스 호출
   - 모듈러 컴포넌트 시스템 등록

3. **PostInitializeComponents**:
   - AbilitySystemComponent 액터 정보 초기화
   - Owner와 Avatar 모두 GameState로 설정
   

#### 초기화 시퀀스
![](/assets/images/old/06e84640-dfbc-4113-8e14-38ba1a8c7557-image.png)


#### Experience 로딩 시퀀스
![](/assets/images/old/1c522480-2670-4fd7-9cdd-3e0ce4b38caf-image.png)


### 2. 네트워크 복제 시스템

#### 복제되는 속성들:
- **ServerFPS**: 서버의 FPS 정보를 모든 클라이언트에 전송
- **RecorderPlayerState**: 리플레이 재생 시에만 복제 (COND_ReplayOnly)

#### 메시지 전송 시스템:
- **MulticastMessageToClients**: 비신뢰성 메시지 전송 (성능 우선)
- **MulticastReliableMessageToClients**: 신뢰성 메시지 전송 (전달 보장)

### 3. 플레이어 관리

- **AddPlayerState**: 새 플레이어 참여 시 호출
- **RemovePlayerState**: 플레이어 퇴장 시 호출 (현재 AGameModeBase에서 직접 호출되지 않는 문제 존재)
- **SeamlessTravelTransitionCheckpoint**: 맵 전환 시 비활성 플레이어와 봇 제거

### 4. 리플레이 시스템

- **RecorderPlayerState**: 리플레이 녹화한 플레이어 상태 저장
- **OnRecorderPlayerStateChangedEvent**: 리플레이 플레이어 변경 이벤트
- 리플레이 재생 시 카메라 시점 결정에 활용

## Experience 시스템 통합

### Experience 로딩 과정

1. **Experience 설정**: `SetCurrentExperience()` 호출
2. **에셋 로딩**: Experience Definition과 관련 에셋들 로딩
3. **Game Feature Plugin 활성화**: Experience에 정의된 플러그인들 활성화
4. **Action 실행**: Experience에 정의된 액션들 실행
5. **로딩 완료**: 다양한 우선순위의 델리게이트 브로드캐스트

### Experience 상태 관리

```cpp
enum class ELyraExperienceLoadState
{
    Unloaded,                    // 로딩되지 않음
    Loading,                     // 로딩 중
    LoadingGameFeatures,         // Game Feature Plugin 로딩 중
    LoadingChaosTestingDelay,    // 테스트용 지연
    ExecutingActions,            // 액션 실행 중
    Loaded,                      // 로딩 완료
    Deactivating                 // 비활성화 중
};
```

