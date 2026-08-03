---
title: "[Lyra 코드 분석] Experience와 게임 초기화 흐름"
description: "Lyra 프로젝트는 Epic Games에서 공식적으로 제공하는 멀티플레이어 슈팅 게임 템플릿으로, 최신 언리얼 엔진 5의 구조와 기능을 실제 게임에 어떻게 적용하는지 잘 보여줍니다."
date: 2025-06-04T11:31:33.719Z
tags: ["ue5","코드분석"]
image:
  path: /assets/images/old/cba3ea5a-5013-4b18-bc20-b928b010ebf5-image.png
---
![](/assets/images/old/cba3ea5a-5013-4b18-bc20-b928b010ebf5-image.png)

Lyra 프로젝트는 Epic Games에서 공식적으로 제공하는 멀티플레이어 슈팅 게임 템플릿으로, 최신 언리얼 엔진 5의 구조와 기능을 실제 게임에 어떻게 적용하는지 잘 보여줍니다. 또한, 단순한 예제 수준을 넘어 Epic Games가 권장하는 최신 설계 표준과 Best Practice를 집대성한 프로젝트입니다.

이 시리즈에서는 Lyra 프로젝트의 핵심적인 코드와 주요 시스템을 AI와 함께 분석하며, 실제 게임 개발에 참고할 수 있는 설계 패턴과 구현 방법을 제 나름대로 정리하여 글로 작성해 보고자 합니다.

아직 많은 것이 부족한 개발자이기 때문에 틀린 내용이 있을 수 있다는 것과, 틀린 점을 발견하셨다면 해당 피드백을 댓글로 공유해주시면 정말 감사합니다.

## GameMode와 Experience
Lyra에서는 전통적인 GameMode와 다르게 Experience라는 개념을 도입하여 함께 사용합니다. 여기서 Experience는 해당 프로젝트에서 전체 게임 모드의 설정, 규칙, 사용 시스템, 액터, UI, 입력 방식 등 게임플레이의 **"상태와 환경"을 정의하는 데이터 구조**라고 합니다. 

Experience는 주요 게임 플레이 요소들의 초기화와 구성을 한번에 관리하며, 매치 시작, 모드 변경, 맵 로딩, 심지어는 실시간 중간 변경까지 "게임의 룰셋 및 환경"을 **동적으로 전환할 수 있도록 설계**되었습니다. 즉, 여러가지의 게임 모드를 수행해야하는 Lyra의 특성과 잘 어울리는 "플러그형 게임 환경 설계"의 핵심이 Experience입니다.

## Experience의 클래스와 간접한 클래스들
Lyra에서는 다음과 같은 클래스를 통해 Experience를 구현합니다.
- **ULyraExperienceDefinition**
Experience 정의의 핵심 클래스. 다양한 Asset/DataTable로 세팅 가능

- **ULyraExperienceManagerComponent**
GameState에 붙어서 Experience를 관리하고, 변경 및 적용을 처리

- **ULyraGameMode, ULyraGameState, ULyraPlayerController, ULyraPlayerState**
Experience 적용 대상이 되는 핵심 액터들



## 게임 시작 로직의 흐름
|  단계 | 함수명                                         | 역할 요약                                      |
| :-: | :------------------------------------------ | :----------------------------------------- |
|  1  | 생성자                                         | GameMode 기본 세팅, Pawn/Controller/HUD 클래스 지정 |
|  2  | InitGame                                    | 맵/옵션 파싱, Experience 할당 예약                  |
|  3  | HandleMatchAssignmentIfNotExpectingOne      | ExperienceId 결정, OnMatchAssignmentGiven 호출 |
|  4  | OnMatchAssignmentGiven                      | ExperienceManager에 ExperienceId 전달, 로딩 시작  |
|  5  | InitGameState                               | GameState 초기화, Experience 로딩 완료 이벤트 등록     |
|  6  | OnExperienceLoaded                          | Pawn/HUD/무기/룰 등 Experience 기반 초기 세팅        |
|  7  | HandleStartingNewPlayer\_Implementation     | Experience가 준비되었을 때만 플레이어 스폰               |
|  8  | ChoosePlayerStart\_Implementation           | 스폰 위치 결정 (PlayerSpawningManager 활용)        |
|  9  | SpawnDefaultPawnAtTransform\_Implementation | Experience의 PawnData를 기반으로 Pawn 스폰         |
|  10 | FinishRestartPlayer                         | Pawn 리스폰/초기화 마무리 작업                        |
|  11 | 그 외                                         | 리스폰, 팀 변경, 매치 교체 등도 Experience 기반          |

1. **GameMode 인스턴스 생성**
언리얼 엔진에서는 맵(World)이 로딩될 때, **UEngine -> UGameInstance -> UWorld** 순으로 월드와 맵을 생성합니다. 이 과정에서 서버는 GameMode를 생성합니다(UWorld::InitializeActorsForPlay()에서 결정 후 생성).
2. **InitGame**
GameMode의 생성자에서 AGameModeBase::InitGame()을 호출합니다. 이 때 Lyra에서는 이 함수를 오버라이드 합니다(ALyraGameMode::InitGame).
이때, ALyraGameMode::InitGame()은 HandleMatchAssignmentIfNotExpectingOne()을 다음 프레임에 예약합니다.
```
// Wait for the next frame to give time to initialize startup settings
GetWorld()->GetTimerManager().SetTimerForNextTick(this, &ThisClass::HandleMatchAssignmentIfNotExpectingOne);
```
**이때, HandleMatchAssignmentIfNotExpectingOne()이 바로 실행되지 않고, 다음 프레임에 실행함으로써, 초기화 순서의 안전성을 보장합니다.** 또한, 이 방법은 다른 초기화 함수에서도 계속 사용됩니다.

다음 프레임에 실행되도록 예약하는 이유는 다음과 같습니다.
- **언리얼 라이프사이클의 현실적인 문제**
  - InitGame()은 GameMode 생성 이후,
"레벨 로딩은 되었지만 아직 완전히 모든 시스템/플러그인/컴포넌트가 초기화되지 않은 시점"에서 호출됩니다.
  - GameState, PlayerState, WorldSettings, ExperienceManager 등 연관 시스템이 아직 완전히 활성화 전일 수 있기 때문입니다.
  - 월드의 다양한 매니저(Subsystem/Component)가 “다음 프레임”에야 완전히 붙는 경우가 많습니다.
- **Experience 로딩의 본질적 특성**
  - Lyra의 Experience 시스템은 "매치가 시작될 때 즉시 로딩/세팅"이 매우 중요합니다 (동적으로 변환되는 것이 목적이기 때문)
   - 그런데 만약 Experience를 너무 빨리 세팅하려 하면 
     - ExperienceManagerComponent를 찾지 못하거나
     - GameState, 월드 세팅 등이 아직 준비되지 않아 null 포인터 등 문제가 발생할 수 있습니다.

즉, Experience가 반영되기 전에 플레이어 스폰 등 후속 로직이 조기 실행될 위험이 있습니다. 따라서, SetTimerForNextTick()을 사용함으로써 현재 프레임의 모든 BeginPlay, 컴포넌트/Subsystem 초기화가 끝나고, 월드가 완전히 안정화된 뒤에 안전하게 Experience 할당/로딩을 하도록 설계한 것입니다.


3. **Experience(경험) 결정 및 로딩**
ALyraGameMode::HandleMatchAssignmentIfNotExpectingOne()이 실행되면 어떤 Experience를 사용할지 결정 (커맨드라인/월드설정/디폴트 등에서 선택)합니다. 이때, Experience을 결정할 때에는 우선순위가 정해져있습니다. 이후 OnMatchAssignmentGiven(ExperienceId, Source) 호출합니다.
```
	// Precedence order (highest wins)
	//  - Matchmaking assignment (if present)
	//  - URL Options override
	//  - Developer Settings (PIE only)
	//  - Command Line override
	//  - World Settings
	//  - Dedicated server
	//  - Default experience
```

4. **ALyraGameMode::OnMatchAssignmentGiven**
선택된 ExperienceId를 GameState의 ExperienceManagerComponent에 전달합니다.
→ ExperienceManagerComponent.SetCurrentExperience(ExperienceId)
Experience 에셋과 연결된 GameFeature, 액션, PawnData, HUD 등 비동기 로드를 시작합니다.

5. **GameState 초기화**
ALyraGameMode::InitGameState()가 호출됩니다. 실제로는 HandleMatchAssignmentIfNotExpectingOne()보다 먼저 수행될 것입니다. (한 프레임 뒤로 예약되어 있기 때문)
GameState 등 주요 시스템을 초기화하고, GameState의 ExperienceManagerComponent에
OnExperienceLoaded 델리게이트(이벤트)를 등록합니다. 그 후 Experience 로딩 완료를 대기합니다.
6. **Experience 로딩 완료**
ALyraGameMode::OnExperienceLoaded(CurrentExperience)가 호출됩니다. 이 시점에는 Experience의 모든 구성요소(플러그인, PawnData, HUD, RuleSet, Action 등)가 로드 완료되었습니다. 또한, 이미 접속한 모든 플레이어 컨트롤러에 대해 Pawn 스폰/리스타트(Respawn)을 시도합니다. 이때  Experience 정보에 맞는 Pawn, HUD, 무기, 룰, UI 등이 적용됩니다.
7. **플레이어 접속/스폰**
게임이 진행중이라고 가정했을 때, 현재 플레이어가 게임에 접속 했을 때는 두가지 경우가 존재할 것입니다.
- 플레이어가 접속할 때(이미 접속해 있는 플레이어들의 Pawn이 존재하는 경우)
  - PreLogin/Login/PostLogin (엔진 기본) 순서로 호출
  - Lyra에서는 Experience가 완전히 로드되기 전에는 바로 Pawn을 스폰하지 않음
(HandleStartingNewPlayer_Implementation에서 Experience가 준비될 때까지 대기)
- Experience 로딩 후, 또는 플레이어 최초 접속시( 플레이어 접속 이후에 또 다른 플레이어가 접속하여 새로운 Pawn 생성되는 경우)
  - HandleStartingNewPlayer_Implementation Experience가 준비된 경우에만, Super::HandleStartingNewPlayer_Implementation(NewPlayer) 호출 → Pawn 스폰

8. **Pawn 스폰 과정**
PlayerSpawningManagerComponent가 스폰 위치를 결정합니다. (ChoosePlayerStart_Implementation() 호출)
SpawnDefaultPawnAtTransform_Implementation()을 통해 PawnClass, PawnData를 Experience에서 받아 실제 Pawn 생성하고, PawnExtensionComponent에 PawnData를 세팅합니다.
9. **그 이후(게임 진행 중)**
플레이어 리스폰, 팀 변경, 경험 교체 등도 모두 Experience 기반 세팅에 맞춰 자동 진행됩니다.

### 여기서 비동기는 다른 스레드에서 실행된다는 의미가 아닙니다

일반적으로 언리얼에서 BeginPlay()는 액터가 월드에 스폰되고 나서 바로 실행되지만 Experience 로딩은 BeginPlay 이후에 따로 트리거 되어 "완료 시점"을 이벤트로 알려줍니다.
 **=> OnExperienceLoaded()**
 
 즉, 게임 라이프 사이클의 BeginPlay와 분리된 시점에서 로딩됩니다. (BeginPlay는 완료되었을지언정, 게임 시작 준비가 끝난 것은 아니라는 의미)
다른 스레드에서 실행되는 것이 보장되지 않음에도 비동기라고 표현하는 이유는 **"시점의 지연과 완료 시점의 통지"를 의미하는 논리적 비동기이기 때문입니다.**
예를 들어 StartExperience()는 호출되어도 즉시 완료되지 않고, 내부적으로 AssetManager를 통해 로딩을 시작합니다. 그 후 완료 시점을 콜백(OnExperienceLoaded() 등)으로 알려주므로 비동기적 흐름입니다.

좀 더 자세히 들여다보면, Experience의 Load과정은 Primary Asset Manager를 통해 처리되는데, 대표적으로 ExperienceDefinition이 PrimaryAsset으로 관리됩니다. 이 자산은 StartExpereince() 호출 시 LoadPrimaryAsset()을 통해 비동기 로딩됩니다.
이때, 언리얼의 Primary Asset 시스템은 기본적으로 비동기지만, 다른 스레드에서 처리된다고 보장하진 않습니다. 대신 메인 게임 스레드에서 "준비 완료 콜백"이 호출될 뿐, 실제 로딩은 내부적으로 AssetManager에 의해 스케줄됩니다.

결론적으로 비동기라는 의미는 게임 로직보다 늦게 완료된다는 의미입니다. 따라서 OnExperienceLoaded() 같은 이벤트를 통해 후속 처리합니다.

## 결국 언리얼의 라이프사이클만으로는 한계가 있다
Lyra는 비동기 방식으로 Experience를 로드하기 때문에, 무엇이 먼저 메모리에 올라올지 예측할 수 없습니다. 이러한 특성으로 인해, 논리적 실행 순서를 보장하기 위해 특정 함수는 1프레임 뒤에 호출되도록 설계되어 있습니다.
**대표적인 예시 => HandleMatchAssignmentIfNotExpectingOne()**
또한, 게임 시작은 반드시 OnExperienceLoaded 이후에 진행해야 합니다.
BeginPlay()에서 바로 게임 로직을 시작하면, Experience에 포함된 Game Feature Plugin, 액션 세트, Pawn Data 등의 준비가 완료되지 않아 불안정하거나 예기치 못한 동작이 발생할 수 있습니다. 따라서 OnExperienceLoaded를 기준으로 후속 로직을 설계해야 안전한 게임 초기화가 가능합니다.

**이러한 구조는 언리얼의 기존 라이프사이클(예: BeginPlay(), InitializeComponent())만으로는 비동기 로딩에 충분히 대응하기 어렵다는 것을 시사합니다.**

특히, 컴포넌트 간의 의존성이 있을 경우, 생성 순서를 명시적으로 제어할 수 없기 때문에 먼저 로드되어야 하는 컴포넌트가 준비되지 않아 에러가 발생할 수 있습니다.

언리얼 엔진은 아니지만 저의 실제 경험으로 한번 더 예시를 들자면, 게임 시작과 동시에 Event Manager와 이 Event Manager에 바인딩 하는 Game Object(언리얼 에서는 Actor)가 생성되는데, 이 2개의 인스턴스가 생성되는 순서가 항상 달랐기 때문에 간헐적으로 오류가 발생했었습니다.

따라서 비동기 로딩 기반 구조에서는, 명확한 초기화 순서를 정의하고 이를 보장할 수 있는 이벤트 기반 설계나 지연 초기화 전략을 반드시 도입해야 합니다.
그렇지 않으면, 순서 의존적인 컴포넌트 간 상호작용에서 예기치 못한 버그가 발생할 수 있습니다.
