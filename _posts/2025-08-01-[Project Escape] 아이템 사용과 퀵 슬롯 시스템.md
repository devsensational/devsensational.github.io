---
title: "[Project Escape] 아이템 사용과 퀵 슬롯 시스템"
description: "땅에 떨어진 아이템을 플레이어가 주웠을 때 실행되어야 하는 로직은 매우 다양하며, 해당 아이템이 사용될 때의 동작 또한 제각각입니다. "
date: 2025-08-01T11:56:00.327Z
tags: ["Project Escape","UE5"]
thumbnail: /assets/images/old/9758d8db-da0a-4680-8a6e-7cabbc39982a-image.webp
---
# 기능에 대한 고찰


기획 단계에서, 저희 팀은 장비 칸과 슬롯형 인벤토리가 분리되어 있는 형태의 인벤토리 시스템을 만들기로 결정했습니다. 이는 'APEX Legends'의 인벤토리 구조에서 착안한 것으로, 해당 게임처럼 무기 칸과 일반 아이템 슬롯이 구분되어 있으며, 키 입력을 통해 인벤토리에 있는 무기나 아이템을 사용할 수 있도록 구성하고자 했습니다. 해당 게임과 다른 점은 무기 칸에 들어갈 아이템 군이 주무기, 보조무기, 근접무기, 투척무기로 분류되었으며, 추가로 체력 회복 아이템이 포함됩니다. 아래 사진은 팀원 분께서 만들어주신 인벤토리 UI의 프로토타입입니다.
![](/assets/images/old/659a8d14-2f27-4459-a181-4e821decac1a-image.png)

이러한 구조를 구현하기 위해 실제 게임 내 아이템의 사용 방식과 패턴을 분석했고, 그 결과 다음과 같은 특징들을 도출할 수 있었습니다.

| 아이템 유형 | 슬롯에 들어감 | 전용 슬롯 장착 가능 | 손에 들 수 있음 |
|-------------|----------------|----------------------|------------------|
| 무기      | ❌             | ✅                   | ✅               |
| 소모성 아이템      | ✅             | ✅                   | ✅               |
| 탄약      | ✅             | ❌                   | ❌               |

땅에 떨어진 아이템을 플레이어가 주웠을 때 실행되어야 하는 로직은 매우 다양하며, 해당 아이템이 사용될 때의 동작 또한 제각각입니다. 초기에는 모든 아이템을 ItemBase 클래스로부터 상속받아 처리하는 방식을 고려했지만, 이 경우 아이템 유형이 많아질수록 클래스 구조가 지나치게 복잡해질 것으로 예상되었습니다.

또한, 동일한 기능을 갖는 클래스임에도 불구하고 일부 클래스에서는 특정 기능이 필요 없거나 동작하지 않는 경우가 발생할 수 있어, 유지보수성과 확장성 측면에서도 한계가 있었습니다.

이에 따라, 저희는 무기와 아이템을 별개의 클래스로 분리하고, 각 클래스의 특성과 용도에 맞는 컴포넌트를 조합하여 기능을 구성하는 방식으로 방향으로 결정했습니다. 이를 통해 공통된 기능은 컴포넌트로 모듈화하고, 필요한 기능만 선택적으로 부착함으로써 보다 유연하고 관리하기 쉬운 구조를 갖출 수 있게 되었습니다.

# 구조 설계
## Interact Component
먼저, 무기나 아이템을 줍기 위해 상호작용 하는 로직을 만들어야 합니다. 이전 사이드 프로젝트에서 구현한 컴포넌트를 해당 프로젝트에 맞게 수정하여 사용하도록 하였습니다. 해당 컴포넌트는 피상호작용 액터를 위한 컴포넌트와 상호작용을 수행하는 액터를 위한 컴포넌트 두개로 나눠져 있습니다. 또한, 컴포넌트 오너와 결합도를 낮추기 위한 인터페이스를 사용합니다.

### UPEInteractManagerComponent
플레이어가 조종하는 캐릭터에 붙어 상호작용을 수행하고, 판정하는 컴포넌트 입니다.

>
**구현해야 하는 기능**
 1. 상호작용 가능한 액터를 Ray 캐스팅으로 감지하는 기능
 2. 상호작용 가능한 액터와의 거리를 계산하여 상호작용 가능한지 여부를 판단하는 기능
 3. 상호작용 입력을 처리하는 기능
 4. 상호작용 가능한 액터와의 상호작용을 실행하는 기능
 
 **실행 순서**
 >
1. 플레이어 입력 (Interact Action)
   ↓
2. UPEInteractManagerComponent::OnInteractPressed()
   ↓
3. UPEInteractManagerComponent::TryInteract()
   - CheckAndSetForInteractable() 호출로 Ray Casting 실행
   - 상호작용 가능한 객체 감지
   ↓
4. UPEInteractableComponent::Interact()
   - IPEInteractable 인터페이스를 통해 아이템의 상호작용 로직 실행
   ↓
5. AFPSTestBlockCharacter::TryInteract() (인터페이스 콜백)
   - 아이템에서 PEQuickSlotItemComponent 검색
   - 퀵슬롯에 아이템 등록
  
   
### UPEInteractableComponent
Interact Manager Component에 의해 상호작용 대상이 되는 액터에 붙는 컴포넌트입니다. 상호작용이 수행되면 컴포넌트 오너에게 상호작용을 호출합니다.

## QuickSlot Component
이제 아이템과 상호작용한 후에는 아이템이 인벤토리에 보관되어야 합니다. 퀵 슬롯은 해당하는 아이템이 전용 슬롯에 장착되도록 관리합니다. 

### UPEQuickSlotManagerComponent
플레어어가 조종하는 캐릭터에 부착되어 퀵슬롯을 관리하는 컴포넌트입니다. 

>
**구현해야 하는 기능**
 1. 퀵슬롯 아이템을 설정하는 기능
 2. 퀵슬롯 아이템을 제거하는 기능
 3. 퀵슬롯 아이템을 선택하는 기능
 4. 퀵슬롯 아이템을 초기화하는 기능
 
 >
 1. AFPSTestBlockCharacter::TryInteract()
   ↓
2. TargetActor에서 UPEQuickSlotItemComponent 검색
   ↓
3. UPEQuickSlotManagerComponent::SetQuickSlotItem()
   - EPEEquipmentType을 키로 사용하여 TMap에 저장
   - 무기 타입별 분류 관리
   ↓
4. 자동 장착 로직
   - ContainWeaponType() 확인
   - HandEquipment() 자동 호출
  
 
 ### UPEQuickSlotItemComponent
 퀵슬롯에 저장되는 아이템을 위한 컴포넌트입니다. 아이템이 주워졌을 때, 버려졌을 때 등의 기능이 자동으로 호출됩니다.
 
 ## Useable Item Component
 킉슬롯에 아이템이 저장되었다면 이제 손에 들고 사용할 수 있도록 해야 합니다. 퀵 슬롯으로 부터 받은 아이템 액터 레퍼런스를 이용하여 아이템을 사용하도록 설계했습니다.
 
 ### UPEUseableItemManagerComponent
 플레어어가 조종하는 캐릭터에 부착됩니다. 아이템을 손에 들 때 사용되며, 해당하는 아이템의 레퍼런스를 포인터에 저장하고, 입력이 들어오면 아이템 사용 함수를 호출합니다.
 
 >
**구현해야 하는 기능**
 1. 아이템을 손에 드는 기능 (Actor Reference)
 2. 아이템을 해제하는 기능 (Actor Reference 해제)
 3. 현재 손에 들고 있는 아이템을 반환하는 기능
 4. 현재 손에 들고 있는 아이템을 사용하는 기능

>
1. 플레이어 입력 (Use Action)
   ↓
2. AFPSTestBlockCharacter::Use()
   ↓
3. UPEUseableItemManagerComponent::UseCurrentItem()
   ↓
4. UPEUseableComponent::Use()
   ↓
5. IPEUseable 인터페이스를 통해 아이템의 실제 Use() 메서드 호출

### UPEUseableComponent
실제로 캐릭터에 의해 아이템이 사용될 액터를 위한 컴포넌트입니다. 

# 구현 및 테스트
![](/assets/images/old/9758d8db-da0a-4680-8a6e-7cabbc39982a-image.webp)
Interact용 Collision에 Ray가 닿으면 아이템이 장착되고, 같은 분류의 아이템이 추가로 상호작용되면 변경되는 모습을 볼 수 있습니다.