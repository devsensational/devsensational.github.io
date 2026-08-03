---
title: "[Project Arc] 네트워크 환경에서 플레이어 카메라 Activate 문제 해결"
description: "오늘은 언리얼 멀티플레이 환경에서 플레이어 카메라 시점이 보이지 않는 문제를 Activate로 해결한 과정과, 아직 남아 있는 카메라 회전(Input_Look) 문제를 원인 중심으로 정리하고자 합니다."
date: 2026-01-07T12:30:39.428Z
tags: ["Project ARC","UE5","트러블슈팅"]
image:
  path: /assets/images/old/6c9f5fa7-c534-46a0-9baf-79f964759010-image.webp
categories: [Project CM + Project Arc]
---
![](/assets/images/old/6c9f5fa7-c534-46a0-9baf-79f964759010-image.webp)


오늘은 언리얼 멀티플레이 환경에서 **플레이어 카메라 시점이 보이지 않는 문제를 Activate로 해결한 과정**과, 아직 남아 있는 **카메라 회전(Input_Look) 문제**를 원인 중심으로 정리하고자 합니다.

---

## 문제 상황 요약

- 환경: UE5, 멀티플레이(Host + Client), C++ 기반 캐릭터/컨트롤러, BP 기반 GameplayCamera 사용
- 증상 1: Client 입장에서 플레이어 Pawn 은 스폰되고 Possess 도 되지만, **카메라 시점이 비어 있거나 이상한 위치를 비춤**
- 증상 2: Host 에서는 정상 동작하는 것처럼 보이지만, **Client 쪽에서만 카메라 관련 문제 발생**
- 추가 증상: 시점을 보이게 만드는 문제는 해결했지만, **마우스 입력에 따른 카메라 상하좌우 회전은 아직 제대로 동작하지 않음**

---

## 원인 분석: 카메라 시점(Activate) 문제

### 1. ViewCamera vs GameplayCamera 사용 불일치

- C++ `ACMPlayerCharacterBase` 안에는 `ViewCamera(UCameraComponent)` 와 `CameraBoom(USpringArmComponent)` 가 존재
  - `CameraBoom->bUsePawnControlRotation = true;`
  - `ViewCamera->bAutoActivate = false;`
- 하지만 실제 게임에서는 캐릭터 BP 에서 **별도의 GameplayCamera 컴포넌트(UGameplayCameraComponent 파생 BP)** 를 메인 카메라로 사용 중
- 결과적으로:
  - C++에서 `ViewCamera->Activate()` 를 호출해도 **실제로 화면에 쓰이는 카메라는 GameplayCamera** 이므로, 시점 문제는 그대로 유지

### 2. 네트워크에서 Possess/BeginPlay 타이밍 차이

- 서버:
  - GameMode 에서 Pawn 생성 → `NewPlayer->Possess(NewPawn)` 실행
  - 서버 기준에서는 Possess 타이밍이 확실
- 클라이언트:
  - Pawn 이 복제되고 `BeginPlay` 가 먼저 호출된 뒤에,
  - 컨트롤러 소유 정보가 들어오고 `PawnClientRestart`/`OnRep_Controller` 등이 호출됨
- `BeginPlay` 기준으로 카메라 Setup 을 시도하면:
  - Host(리스너 서버)는 우연히 잘 동작할 수 있지만,
  - 순수 Client 에서는 **아직 로컬 컨트롤러가 붙지 않은 상태**일 수 있어서 `IsLocallyControlled()` 가 false 인 경우가 많음
  - 이 경우, 로컬 전용 카메라 Activate 로직이 실행되지 않음

---

## 해결 전략: PawnClientRestart에서 GameplayCamera Activate

### 선택한 기준 시점

- 네트워크 플레이에서 **로컬 클라이언트가 이 Pawn 을 실제로 조종할 준비가 된 시점**은 `APawn::PawnClientRestart()` 에서 가장 확실
- 이유:
  - 컨트롤러/Owner 정보가 세팅된 뒤 호출됨
  - 입력 매핑(Enhanced Input)도 이 시점에 다시 셋업하는 패턴이 일반적
  - Host / Client 양쪽에서 동일한 타이밍 보장

### 구현 아이디어

- `ACMPlayerCharacterBase` 에 **카메라 셋업 전용 헬퍼 함수** 추가
  - `UGameplayCameraComponent` 를 `FindComponentByClass` 로 찾아온다.
  - 해당 컴포넌트에 대해 `Activate()` (또는 `SetupCamera()`) 를 호출한다.
- `PawnClientRestart()` 에서:
  - 기존 입력 매핑 설정 후
  - 바로 이 헬퍼 함수를 호출하여, 로컬 플레이어의 카메라를 활성화한다.

---

## 적용한 헬퍼 함수 소스코드

### 1. 헤더 선언 (ACMPlayerCharacterBase.h)

- 전방 선언 및 private 헬퍼 함수 선언

```cpp
class UGameplayCameraComponent;

UCLASS()
class CRIMSONMOON_API ACMPlayerCharacterBase : public ACMCharacterBase
{
	GENERATED_BODY()

	// ...existing code...

private:
	// BeginPlay 이후, 로컬 플레이어 기준으로 GameplayCamera를 셋업하는 헬퍼 함수
	void SetupGameplayCamera_Helper();

	// ...existing code...
};
```

### 2. 구현부 (ACMPlayerCharacterBase.cpp)

```cpp
void ACMPlayerCharacterBase::SetupGameplayCamera_Helper()
{
	UE_LOG(LogTemp, Warning,
		TEXT("SetupGameplayCamera_Helper: Called. IsLocallyControlled=%d"),
		IsLocallyControlled() ? 1 : 0);

	// 로컬 플레이어가 소유한 Pawn 에서만 카메라 셋업
	if (!IsLocallyControlled())
	{
		UE_LOG(LogTemp, Warning,
			TEXT("SetupGameplayCamera_Helper: Aborted - not locally controlled"));
		return;
	}

	// BP 에서 추가된 UGameplayCameraComponent 를 찾아 SetupCamera/Activate 호출
	if (UGameplayCameraComponent* GameplayCameraComp = FindComponentByClass<UGameplayCameraComponent>())
	{
		UE_LOG(LogTemp, Warning,
			TEXT("SetupGameplayCamera_Helper: Found GameplayCameraComponent on %s, calling SetupCamera"),
			*GetName());

		// 현재는 Activate로 시점을 살려두었음 (필요 시 SetupCamera()로 교체 가능)
		GameplayCameraComp->Activate();
		// GameplayCameraComp->SetupCamera();
	}
	else
	{
		UE_LOG(LogTemp, Warning,
			TEXT("SetupGameplayCamera_Helper: GameplayCameraComponent not found on %s"),
			*GetName());
	}
}
```

#### PawnClientRestart에서 호출

```cpp
void ACMPlayerCharacterBase::PawnClientRestart()
{
	Super::PawnClientRestart();

	if (const APlayerController* OwningPlayerController = GetController<APlayerController>())
	{
		UEnhancedInputLocalPlayerSubsystem* PlayerSubsystem =
			OwningPlayerController->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>();

		check(PlayerSubsystem);

		PlayerSubsystem->RemoveMappingContext(InputConfigDataAsset->DefaultMappingContext);
		PlayerSubsystem->AddMappingContext(InputConfigDataAsset->DefaultMappingContext, 0);
	}

	// 로컬 클라이언트가 이 Pawn 을 다시 사용할 준비가 된 시점에 카메라 셋업 시도
	SetupGameplayCamera_Helper();
}
```

---

## 현재 상태: 시점 문제는 해결, 회전 문제는 미해결

![](/assets/images/old/19725d02-0b07-403c-b24d-382cdcf5fc10-image.webp)

### 해결된 부분

- Host / Client 모두에서:
  - GameplayCameraComponent 를 **로컬 클라이언트 기준으로 Activate** 하도록 변경
  - PawnClientRestart 기준으로 실행되기 때문에, 네트워크 타이밍 문제(컨트롤러 미소유 상태)는 피함
- 결과적으로:
  - **카메라 시점이 비어 있거나, 이상한 곳을 비추던 문제는 해결**됨
  - 캐릭터를 정상적으로 화면에 비추고, 이동/전투 플레이가 가능해짐

### 아직 해결되지 않은 부분: 마우스 입력에 따른 카메라 회전

- 남아 있는 문제:
  - 마우스 입력(`Input_Look`)에 따라 카메라가 **상하좌우로 자연스럽게 회전해야 하는데**,
  - 지금은 시점은 잡히지만, **회전이 작동하지 않음**
- 추정 원인:
  - C++ 측에서는 `Input_Look` 에서 `AddControllerYawInput`, `AddControllerPitchInput` 을 호출하고 있음
  - 하지만 실제로 화면에 쓰이는 것은 **BP 기반 GameplayCamera** 이고,
  - 이 GameplayCamera/SpringArm 이 컨트롤러 회전을 제대로 반영하지 않거나,
    - `bUsePawnControlRotation` 설정이 비활성화되어 있거나,
    - 자체 로직으로만 회전을 제어하고 있을 가능성이 큼
  - 따라서 **컨트롤러 회전 값은 변하지만, 카메라 컴포넌트가 그 값을 사용하지 않는 상태**일 수 있음
- 요약:
  - "카메라가 안 보인다" 문제는 `UGameplayCameraComponent` Activate 로 해결
  - "카메라가 마우스 입력대로 돌지 않는다" 문제는 **GameplayCamera의 회전 설정/로직 조정**이 추가로 필요

---

## 마치며

이번 작업에서는 네트워크 환경에서 플레이어 카메라 시점이 비정상적으로 비춰지는 문제를, `PawnClientRestart` 시점에 `UGameplayCameraComponent` 를 찾아 Activate 하는 방식으로 해결하였습니다. 특히 BeginPlay, PossessedBy, PawnClientRestart 간의 호출 시점과 `IsLocallyControlled()` 여부가 네트워크 환경에서 어떻게 달라지는지 다시 한 번 정리할 수 있었고, 로컬 전용 카메라 로직은 PawnClientRestart 에서 처리하는 것이 안전하다는 점을 확인했습니다.

다만, 아직 마우스 입력에 따른 카메라 상하좌우 회전이 기대한 대로 동작하지 않는 문제가 남아 있습니다. 이는 C++ 단의 Input_Look 처리가 아니라, 실제 뷰를 담당하고 있는 GameplayCamera 컴포넌트의 회전 설정과 로직이 컨트롤러 회전을 어떻게 받아들이는지에 더 가깝기 때문에, 다음 단계에서는 해당 BP/컴포넌트의 `bUsePawnControlRotation` 설정, SpringArm 사용 여부, ViewTarget 세팅 방식을 집중적으로 점검하고 수정할 예정입니다.

