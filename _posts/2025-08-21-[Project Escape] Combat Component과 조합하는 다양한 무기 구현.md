---
title: "[Project Escape] Combat Component과 조합하는 다양한 무기 구현"
description: "게임을 개발하다 보면 무기를 구현하는 과정에서 반복되는 로직과 복잡한 의존성이 큰 골칫거리가 되곤 합니다. 특히 근접 무기, 특수 무기처럼 형태는 달라도 공통적으로 `공격한다`는 기능을 가지기 때문에, 이를 어떻게 유연하고 확장 가능하게 설계할지가 핵심 과제입니다"
date: 2025-08-21T11:00:24.601Z
tags: ["project escape","ue5"]
image:
  path: /assets/images/old/ff210be0-a40e-4832-8b27-8f096b978580-image.gif
---
게임을 개발하다 보면 무기를 구현하는 과정에서 반복되는 로직과 복잡한 의존성이 큰 골칫거리가 되곤 합니다. 특히 총기, 근접 무기, 특수 무기처럼 형태는 달라도 공통적으로 "공격한다"는 기능을 가지기 때문에, 이를 어떻게 유연하고 확장 가능하게 설계할지가 핵심 과제입니다.

이번 글에서는 Combat Component를 중심으로 무기 시스템을 설계하고, 이를 조합하여 다양한 무기를 구현하는 방법을 소개하려 합니다. 각 무기가 고유의 동작을 가질 수 있도록 컴포넌트를 조합하고 데이터를 수정하여 새로운 무기를 만들어낼 수 있는 구조를 목표로 합니다.

# 히트스캔 vs 투사체, 그리고 산탄의 공통화

무기 시스템을 설계할 때 가장 먼저 고민해야 하는 것은 발사 방식입니다. 크게 히트스캔(라인 트레이스 기반 판정) 과 투사체(액터 스폰 기반 궤적) 로 나눌 수 있습니다.

>**히트스캔: 즉시 판정, 대신 물리적 상호작용 표현이 제한적.**
>**투사체: 곡사, 중력, 폭발, 충돌 규칙 같은 리치한 표현 가능.**

여기에 또 다른 차원의 요구사항이 있습니다. 샷건, 멀티샷처럼 "한 번의 트리거로 여러 발이 발사되는 기능"입니다. 중요한 점은 이 기능이 히트스캔/투사체와 무관하게 공통으로 존재한다는 사실입니다.

따라서 “발사 방식(히트스캔/투사체)” 과 “발사 패턴(단발/연발/산탄)” 을 분리하면 설계와 관리가 훨씬 깔끔해집니다. 즉, 샷건이든, 버스트든, 투사체 로켓런처든, 다발 발사 로직은 하나의 공통 단계(Emission) 로 처리해야 유지보수와 확장이 쉬워집니다.

핵심은 발사를 Trigger → Emission → Ballistics → HitProcess → Effects 의 파이프라인으로 쪼개고, 각 단계를 데이터 기반으로 통합 관리하는 것입니다.

# 구조 설계 및 구현
Project Escape의 무기 시스템은 **“무기가 직접 공격 로직을 갖지 않고, 공격 전담 컴포넌트(AttackComponent)를 생성해서 실행”** 하는 구조를 채택했습니다.

이 방식은 무기가 생성될 때 **가상 팩토리(virtual factory)** 를 통해 공격 방식을 결정하고, 발사 시에는 **공통 AttackStats** 를 AttackComponent에 전달하여 히트스캔 또는 투사체 로직을 실행하도록 합니다.


## 핵심 구조

### 1. 공격 컴포넌트 베이스

* **UPEAttackBaseComponent**

  * 모든 공격 컴포넌트의 공통 베이스.
  * 입력 구조체: **FPEAttackStats** (데미지, 사거리, 퍼짐 각도, 채널, 투사체 클래스/속도 등).
  * 주요 흐름:

    1. `ExcuteAttack` → 공격 시작 위치·방향 계산
    2. `ApplyAccuracyDeviation` → 퍼짐 적용
    3. `PerformAttack` → 구체적 탄도/판정 실행
  * 파티클/사운드 재생 유틸 제공.

### 2. AttackComponent 구현체

* **UPEAttackHitscanComponent**

  * `LineTraceSingleByChannel` 로 즉시 판정.
  * 맞은 컴포넌트가 **UPEReceiveAttackComponent** 일 때만 데미지 처리.

* **UPEAttackProjectileComponent**

  * **APEProjectileBase** 액터를 스폰 후 Launch.
  * Instigator를 무기의 Owner로 전달.
  * 충돌/폭발 로직은 투사체 클래스에서 자체 처리.

### 3. 무기 베이스 클래스

* **APEWeaponBase**

  * `PostInitializeComponents` 시점에 `CreateAttackComponent()` 호출 → AttackComponent 생성 후 `RegisterComponent()`.
  * `CreateAttackComponent` 는 가상 함수 → 파생 무기에서 오버라이드해야 올바른 공격 방식이 동작.
  * **DoPrimaryAction(발사)** 흐름:

    1. 발사 입력 처리 (쿨다운, 연사, 장전 체크)
    2. **FPEAttackStats** 구성 (데미지, 사거리, 퍼짐, 채널 등)
    3. `BulletsPerShot` 만큼 AttackComponent→`ExcuteAttack` 호출

---

## 실행 파이프라인

1. **Interact (집기)**

   * 무기는 소유자(WeaponOwnerActor)를 기억.
   * `IPEAttackable` 인터페이스에서 AttackStartPoint를 받아 AttackComponent에 전달.

2. **DoPrimaryAction (발사 입력)**

   * 발사 가능 여부 확인 (재장전, 연사 제어).
   * AttackStats 구성.
   * BulletsPerShot 횟수만큼 `AttackComponent->ExcuteAttack` 호출.

3. **UPEAttackBaseComponent::ExcuteAttack**

   * AttackStartPoint에서 방향 벡터 산출.
   * SpreadAngle 적용.
   * `PerformAttack` 호출.

4. **구현체별 PerformAttack**

   * **히트스캔**: 라인트레이스 → HitResult 대상이 UPEReceiveAttackComponent일 경우 데미지 처리.
   * **투사체**: Projectile 스폰 후 Launch (시작점, 방향, 속도, 충돌 채널).

5. **피드백 & 상태 갱신**

   * 이펙트/사운드/애니메이션/HUD 업데이트.
   * 탄약 차감 및 상태 브로드캐스트.

## 구현 포인트

### 히트스캔

* `World->LineTraceSingleByChannel(Start, End, AttackStats.HitscanChannel)`
* 자기 자신 무기/소유자는 Ignore 처리.
* 피격 대상 필터링: `HitResult.GetComponent()->IsA(UPEReceiveAttackComponent)`
* 디버그용 DrawDebugLine/Sphere 활용 가능.

### 투사체

* `SpawnActor<APEProjectileBase>(ProjectileClass, StartLocation, …)`
* `SpawnParams.Owner = GetOwner()`, `SpawnParams.Instigator = PawnOwner`
* AlwaysSpawn 옵션으로 충돌 무시 후 스폰.
* Projectile->Launch 호출 시 AttackStats 및 Instigator 전달.
* 충돌 채널은 AttackStats.ProjectileCollisionChannel 로 지정.

## 데이터와 실행의 연결

* 무기 데이터: **DataTable + RowName → FPEWeaponData** 로드.
* 무기는 발사 시 WeaponStats를 AttackStats로 변환.
* **즉, 무기는 데이터와 입력 관리 / AttackComponent는 탄도와 판정 담당**.


# 테스트 및 완성
![](/assets/images/old/f3037da1-b052-4ddb-ba99-4626822bca73-image.gif)

![](/assets/images/old/fe24420b-c2d0-440b-be66-64469d30d5c4-image.gif)

![](/assets/images/old/476a408a-042f-4749-b33a-7e93246748c6-image.gif)

![](/assets/images/old/a1aa8e51-181a-4bb5-b05b-be7c31388bb1-image.gif)



