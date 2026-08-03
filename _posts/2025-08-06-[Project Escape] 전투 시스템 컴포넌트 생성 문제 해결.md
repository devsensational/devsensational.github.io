---
title: "[Project Escape] 전투 시스템 컴포넌트 생성 문제 해결"
description: "컴포넌트가 생성 문제로 에러가 발생했습니다. 이를 해결하기 위한 과정을 확인해보세요."
date: 2025-08-06T11:58:21.621Z
tags: ["project escape","ue5","트러블슈팅"]
image:
  path: /assets/images/old/0f3132d5-bfc6-436e-bfdc-3defa5bf8e9b-image.png
---
# 문제 발생
![](/assets/images/old/0f3132d5-bfc6-436e-bfdc-3defa5bf8e9b-image.png)
팀원 분께서 테스트 중 에디터가 종료되는 오류를 발견하셨습니다. 문제의 액터는 WeaponBase 클래스를 상속받아 생성된 테스트용 임시 무기로, 테스트 필드에 배치되어 사용 중이었습니다. 해당 액터에 상호작용을 시도하는 순간, 에디터가 크래시되었고, 디버깅 결과 다음 위치에서 오류가 발생한 것을 확인할 수 있었습니다.

```cpp
if (IPEAttackable* AttackableInterface = Cast<IPEAttackable>(Interactor))
	{
		AttackComponent->SetAttackStartPoint(AttackableInterface->GetAttackStartPoint()); // 오류 발생 지점
		UE_LOG(LogPE, Log, TEXT("AttackableInterface found and AttackStartPoint set for %s"), *GetNameSafe(Interactor));
	}
   ```
   
  

# 원인 분석
다행히 nullptr가 발생할 수 있는 지점에 대해 if 문과 Cast를 통한 예외 처리를 미리 해두었기 때문에, 문제의 원인이 AttackComponent에 있다는 것을 빠르게 파악할 수 있었습니다. 

AttackComponent는 Weapon 클래스에 부착되어 있으며, Ray 또는 Projectile을 발사하는 역할을 담당하는 컴포넌트입니다.

문제가 발생한 액터는 빨간색으로 표시한 테스트 필드에 배치된 액터로, 원래는 WeaponBase 클래스의 기능을 테스트하기 위해 생성된 것이었습니다. 하지만 이후 WeaponHitscan 클래스를 구현하면서 AttackComponent가 필요한 구조로 변경되었고, 기존의 WeaponBase에는 해당 컴포넌트를 추가하지 않아 nullptr 예외가 발생한 것입니다.


```cpp
//WeaponBase.h
TObjectPtr<UPEAttackBaseComponent> AttackComponent;

//WeaponBase.cpp
APEWeaponBase::APEWeaponBase()
{	
	// 이 곳에는 AttackComponent를 생성하지 않음
     . . .
}

//WeaponHitscan.cpp
APEWeaponHitscan::APEWeaponHitscan()
{
	// 이 곳에서 타입에 맞는 AttackComponent 생성
	AttackComponent = CreateDefaultSubobject<UPEAttackHitscanComponent>(TEXT("AttackComponent"));
    . . .
}    
```
# 해결 과정과 리팩토링
처음에는 WeaponBase의 생성자에 AttackComponent를 추가만 하면 해결될 것이라고 생각했습니다. 하지만 WeaponHitscan의 생성자에서도 AttackComponent를 생성하고 있기 때문에 해결될 수 없었습니다. Base의 생성자가 먼저 호출되어 AttackComponent가 이미 생성되어 있기 때문입니다. 따라서, 기존에 있는 컴포넌트 인스턴스를 제거 후 생성하거나, 타입에 맞는 컴포넌트를 한 번만 생성할 필요가 있습니다.

생성 단계에서는 해결할 수 없기 때문에, 런타임 상황에서 타입에 맞는 컴포넌트를 한 번만 생성하는 것으로 방향을 잡았습니다. 또한, 객체의 다형성을 유지하고, 불필요한 코드를 줄이기 위해 팩토리 패턴을 도입했습니다.

먼저, 컴포넌트 생성 단계 이후 시점에 생성하면 되기 때문에 PostInitializeComponents()를 오버라이드 하여 구현했습니다.
```cpp
void APEWeaponBase::PostInitializeComponents()
{
	Super::PostInitializeComponents();

	if (!AttackComponent)
	{
		AttackComponent = CreateAttackComponent();
		if (AttackComponent)
		{
			AttackComponent->RegisterComponent();
			UE_LOG(LogPE, Log, TEXT("AttackComponent created and registered for %s"), *GetName());
		}
		else
		{
			UE_LOG(LogPE, Error, TEXT("Failed to create AttackComponent for %s"), *GetName());
		}
	}
}
```
여기서 핵심은 CreateAttackComponent() 입니다. 각각의 클래스에서 해당 함수를 오버라이드하여 타입에 맞는 컴포넌트를 생성하는 것입니다.

```cpp
//PEWeaponBase.h
virtual UPEAttackBaseComponent* CreateAttackComponent();

//PEWeaponBase.cpp
UPEAttackBaseComponent* APEWeaponBase::CreateAttackComponent()
{
    return NewObject<UPEAttackBaseComponent>(this);
}

//PEWeaponHitscan.cpp
UPEAttackBaseComponent* APEWeaponHitscan::CreateAttackComponent()
{
	return NewObject<UPEAttackHitscanComponent>(this);
}
```

이로써 에러없이 타입에 맞는 컴포넌트를 동적으로 생성할 수 있게 되었습니다.


# 마치며
이번 문제 해결 과정을 통해 꼼꼼한 예외 처리와 로그 출력의 중요성을 다시금 체감할 수 있었습니다. nullptr에 대한 방어적 조건문과 Cast 체크, 그리고 적절한 위치에 삽입된 로그 덕분에 에디터가 크래시된 직후에도 문제의 원인을 빠르게 좁혀 나갈 수 있었습니다. 프로그램이 강제 종료되지 않고, 충분한 정보를 남긴다는 점은 디버깅 과정에서 큰 이점을 제공합니다. 앞으로도 기능을 구현할 때는 예외 가능성을 염두에 두고, 조기에 감지할 수 있는 로그 체계를 갖추는 것이 중요하다는 교훈을 얻었습니다.

반면, 테스트 환경의 유지 관리에 대한 경각심도 함께 들었습니다. 문제가 발생한 액터는 초기 테스트를 위해 생성된 WeaponBase 인스턴스였지만, 시스템이 확장되어 AttackComponent가 필수 요소로 추가되었음에도 해당 액터에는 이를 반영하지 않아 충돌이 발생했습니다. 임시로 배치한 테스트 자산이 시간이 지나며 시스템 구조와 불일치하게 된다는 점은 예상 밖이었고, 결과적으로 시스템 전체의 안정성을 해칠 수 있는 요인이 되었습니다. 이러한 실수를 줄이기 위해선 기능이 확장될 때마다 기존 테스트 자산의 호환성도 함께 점검하는 습관이 필요합니다.

이번 경험을 통해 단순히 버그를 수정하는 것을 넘어, 테스트 환경의 유지, 방어적인 프로그래밍의 필요성, 그리고 클래스 간 의존성에 대한 명확한 인식까지 얻을 수 있었습니다. 앞으로는 문제가 발생했을 때 그 원인을 단순히 해결하는 데 그치지 않고, 유사한 문제가 재발하지 않도록 시스템 전체를 되돌아보며 예방 전략까지 함께 고민하는 개발 습관을 이어나가려 합니다.