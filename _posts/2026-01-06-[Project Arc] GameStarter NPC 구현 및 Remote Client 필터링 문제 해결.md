---
title: "[Project Arc] GameStarter NPC 구현 및 Remote Client 필터링 문제 해결"
description: "이번에는 멀티플레이 환경에서 게임 시작용 NPC(GameStarter NPC) 를 구현하고, 발생한 문제를 해결했습니다."
date: 2026-01-06T10:29:33.119Z
tags: ["project arc","ue5","troubleshooting"]
image:
  path: /assets/images/old/4d39ae82-62ca-4775-82b5-3d051a9b1f04-image.webp
categories: [Project, Project CM + Project Arc]
---
이번에는 멀티플레이 환경에서 **게임 시작용 NPC(GameStarter NPC)** 를 구현하고, 발생한 문제를 해결했습니다.

목표는 다음과 같습니다.
>
- NPC와 상호작용(Interact)했을 때 **서버 인원 전체**를 특정 맵으로 이동시키기
- 이동 전 **화면이 서서히 어두워지는 연출(페이드 아웃)** 추가
- Interact 로직이 **항상 서버(Host)** 에서만 실행되도록 보장
- 특히, **Remote Client가 조종하는 캐릭터가 Interact를 수행했을 때는 GameStarter 로직이 실행되지 않도록 필터링**

특히, 게임 시작이 Host에서만 수행되도록 해야 하지만, Interact가 서버를 통해 수행되어 의도와 다르게 수행됐던 문제를 중점적으로 다뤄보고자 합니다.

---

## 현재 상호작용(Interact) 구조 분석

### 1. 입력 처리 흐름 (클라이언트)

- 컴포넌트: `UCMPickUpComponent`
- 역할: 입력 바인딩 및 상호작용 대상 관리
- 주요 특징
  - `BeginPlay`에서 입력 시스템 초기화 시도 (`InitializeInputSystem`)
  - 로컬 플레이어 컨트롤러가 준비되면 Enhanced Input으로 Interact 액션 바인딩
  - Tick에서 서버 기준으로 가장 가까운 상호작용 대상(`CurrentInteractableActor`)을 계산 및 복제


- 입력 처리 함수
  - `UCMPickUpComponent::OnPickupInput(const FInputActionValue& Value)`
    - Interact 키(예: `2번`)를 누르면 호출
    - 직접 트레이스를 하지 않고, **Ability System에 태그를 기반으로 Activiate 요청**
    - 코드 요약
      - `AbilitySystemComponent->TryActivateAbilitiesByTag(InteractAbilityTag, true);`
    - 이 부분은 **클라이언트 로컬에서만 실행**됨

### 2. Gameplay Ability 실행 (서버)

- 클래스: `UCMAbility_Interact`
- 역할: Interact Ability의 실제 실행 로직
- 핵심 설정
  - `NetExecutionPolicy = EGameplayAbilityNetExecutionPolicy::ServerOnly;`
  - 의미: Ability의 `ActivateAbility` 는 **항상 서버에서만 실행**


- 실행 흐름 요약
  - `AvatarActor` (보통 플레이어 캐릭터)를 가져옴
  - `AvatarActor`에서 `UCMPickUpComponent`를 찾음
  - `PickUpComp->GetCurrentInteractable()`로 상호작용 대상 `HitActor` 획득
  - `HitActor`가 `UCMInteractableInterface` 구현 시:
    - `ICMInteractableInterface::Execute_Interact(HitActor, AvatarActor);`
  - 어빌리티 종료 (`EndAbility`)


- 시사점
  - Interact 입력은 **클라이언트에서 시작**하지만,
  - 실제 Interact 실행(인터페이스 호출)은 **서버에서 수행**됨

### 3. NPC 인터페이스 및 GameStarter NPC 역할


- 기본 NPC 클래스: `ACMNpcBase`
  - `ICMInteractableInterface` 를 구현
  - 기본적인 상호작용/대화/상점 등 공통 로직 보유


- GameStarter NPC: `ACMNpcGameStarter : public ACMNpcBase`
  - 역할
    - 특정 NPC와의 Interact 시, **서버 전체를 지정 맵으로 이동(ServerTravel)**
    - 이동 직전, 모든 클라이언트 화면을 **서서히 어둡게(페이드 아웃)** 처리
  - 제약 조건
    - **Ability 쪽 코드는 수정하지 않음**
    - 필터링 로직은 **GameStarter NPC 내부에서만 구현**
    - Remote Client가 조종하는 캐릭터의 Interact는 **무시**

---

## GameStarter NPC에서의 Remote Client 필터링 설계

### 1. 요구사항 정리

- Interact 구조(입력 → Ability → 서버에서 Interact 호출)는 그대로 유지
- 단, GameStarter NPC 입장에서 **Interactor가 누구인지 보고** 다음과 같이 처리
  - Interactor가 **Remote 클라이언트가 조종하는 Pawn**이면 → GameStarter 로직 실행 X
  - Interactor가 **리슨 서버(Host)가 조종하는 Pawn** 또는 기타 허용된 주체라면 → GameStarter 로직 실행 O

### 2. 서버 관점에서 Remote Client 판별 기준

- 서버 기준에서 `APawn` 의 `Controller` 를 통해 판별
- 판별 로직
  - `Controller->IsPlayerController() == true` 이면, 플레이어가 조종하는 Pawn
  - 이 때,
    - `Controller->IsLocalController() == true`  → 서버 자신(리슨 서버) 혹은 서버 로컬 컨트롤러
    - `Controller->IsLocalController() == false` → **Remote 클라이언트가 조종 중인 Pawn**
- 따라서 아래 조합으로 Remote 클라이언트를 판별 가능
  - `Controller->IsPlayerController()` && `!Controller->IsLocalController()`


이를 GameStarter NPC의 `Interact_Implementation` 안에서 사용하여 필터링을 구현했습니다.

---

## ACMNpcGameStarter 내부 구현 변화

### 1. 클래스 인터페이스 확장 (헤더)

- 파일: `CMNpcGameStarter.h`
- 변경 사항
  - `Interact_Implementation(AActor* Interactor)` 오버라이드 선언
  - `PerformInteract()` 를 `override` 로 선언해 GameStarter 전용 로직 수행
  - GameStart에 필요한 설정값을 프로퍼티로 추가

- 주요 멤버 요약
  - `virtual void Interact_Implementation(AActor* Interactor) override;`
  - `virtual void PerformInteract() override;`
  - `UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "GameStart") FString TravelURL;`
  - `UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "GameStart") float FadeDuration = 1.0f;`
  - `UFUNCTION(NetMulticast, Reliable) void MulticastStartFadeOut();`
  - `void ServerTravelToConfiguredMap();`

### 2. Interact_Implementation에서 Remote Client 필터링

- 파일: `CMNpcGameStarter.cpp`
- 핵심 로직
  - 오직 **서버(또는 리슨 서버)** 에서만 Interact 처리
  - `Interactor` 가 Remote 클라가 조종하는 Pawn이면 조용히 `return;`
  - 그 외 Interactor에 대해서만 `PerformInteract()` 호출
- 로직 개요
  - 권한 체크
    - `if (!HasAuthority() && GetNetMode() != NM_ListenServer) return;`
  - Interactor 타입 검사
    - `APawn* Pawn = Cast<APawn>(Interactor);`
    - `AController* Controller = Pawn->GetController();`
  - Remote Client 판별
    - `Controller->IsPlayerController() && !Controller->IsLocalController()` → Remote 클라
  - 필터링
    - 위 조건이면 `return;` → GameStart 로직 미실행
  - 허용 시
    - `PerformInteract();` 호출

### 3. PerformInteract: 서버 전용 GameStart 로직

- 역할
  - 서버에서만 실행되는 GameStart 핵심 로직
  - 전체 클라이언트에 페이드 아웃 명령 전파
  - 페이드가 끝난 시점에 ServerTravel 수행
- 동작 순서
  1. `HasAuthority()` + `NetMode` 체크로 서버/리슨 서버에서만 진행
  2. `UWorld* World = GetWorld();` 유효성 확인
  3. `MulticastStartFadeOut();` 호출 → NetMulticast RPC
  4. `World->GetTimerManager().SetTimer(..., FadeDuration);` 로 `ServerTravelToConfiguredMap` 예약 호출
- 이로 인해:
  - 클라이언트가 Interact 입력을 하더라도
  - Ability → 서버에서 Interact → GameStarter → **추가 필터링 후 허용된 경우에만** 서버 트래블이 실행됨

### 4. MulticastStartFadeOut: 모든 클라에서 로컬 화면 페이드

- 함수: `MulticastStartFadeOut_Implementation()`
- 특성: `NetMulticast, Reliable`
  - 서버에서 한 번 호출하면, **서버 + 모든 클라이언트 월드에서 각각 1번씩 실행**
- 동작
  - `UWorld* World = GetWorld();`
  - `APlayerController* PC = World->GetFirstPlayerController();`
  - `PC->IsLocalController()` 인 경우에만 페이드 적용
  - `PC->PlayerCameraManager->StartCameraFade(0.0f, 1.0f, FadeDuration, FLinearColor::Black, true, true);`
- 결과
  - 각 클라이언트가 **자기 화면에서만** 0 → 1 알파로 서서히 어두워짐
  - Remote/로컬 구분 없이, 모든 접속자 화면에서 동일한 페이드 아웃 연출 발생

### 5. ServerTravelToConfiguredMap: 서버 인원 전체 맵 이동

- 역할
  - 에디터에서 설정한 `TravelURL` 을 기준으로 ServerTravel 실행
- 동작 요약
  - 서버/리슨 서버에서만 실행 (`HasAuthority()` 체크)
  - `TravelURL.IsEmpty()` 시 로그만 출력하고 종료
  - `World->ServerTravel(TravelURL, /*bAbsolute*/ false);`
- 효과
  - 서버가 새로운 맵으로 트래블하면서,
  - 현재 접속 중인 모든 클라이언트도 해당 맵으로 함께 이동

---

## 5. 상호작용 흐름 전체 시각화

![](/assets/images/old/1b372dfb-8ac8-4c41-b5a9-b074674b2c59-image.png)


---

## 6. 얻은 인사이트 및 정리

오늘 작업을 통해 다음과 같은 점을 다시 정리할 수 있었습니다.

- **입력과 실행 주체의 분리**
  - 상호작용 입력은 클라이언트에서 발생하지만,
  - 실제 게임 규칙(Logics)은 ServerOnly Ability와 서버 측 NPC 로직을 통해 **서버에서만 결정**하도록 설계할 수 있음


- **Remote Client 필터링은 Interactor 정보를 활용해 GameStart 클래스 내부에서 충분히 처리 가능**
  - Ability 구조를 건드리지 않고도,
  - `Interact_Implementation(AActor* Interactor)` 에서 Interactor의 Controller를 검사하여
  - Remote 클라이언트가 조종하는 Pawn의 Interact만 깔끔하게 차단할 수 있었음


- **NetMulticast + 로컬 컨트롤러 검사로 시각 효과를 안전하게 분배**
  - `NetMulticast` 함수는 월드마다 한 번씩 실행되므로,
  - 함수 내부에서 `GetFirstPlayerController()` + `IsLocalController()` 조합을 사용하면
  - 각 클라이언트의 로컬 화면에만 시각 효과(페이드)를 적용할 수 있음


- **서버 트래블(ServerTravel)과 연출(페이드)을 분리하여 타이밍 제어**
  - 페이드 아웃 → 타이머 → ServerTravel 순으로 분리함으로써,
  - 연출 타이밍과 실제 맵 전환 타이밍을 명확하게 제어할 수 있었음


앞으로는 이 패턴을 바탕으로, 특정 권한(예: GM 전용, 특정 팀 전용)만 사용할 수 있는 상호작용 오브젝트를 설계할 때, Interactor 기반 필터링을 적극적으로 활용할 계획입니다.

