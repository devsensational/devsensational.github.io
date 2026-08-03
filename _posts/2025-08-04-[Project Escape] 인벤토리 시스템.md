---
title: "[Project Escape] 인벤토리 시스템 "
description: "이번에는 탄약, 회복아이템과 같은 가방에 저장할  수 있는 아이템을 위한 컴포넌트를 구현함으로써 유연성 있는 아이템 장착 및 사용 시스템을 구현 해보도록 하겠습니다."
date: 2025-08-04T11:57:00.316Z
tags: ["Project Escape","UE5"]
image:
  path: /assets/images/old/f1243838-5164-47c8-968a-cc0c913d6f2a-image.webp
---
저번 글에서는 '상호작용-퀵 슬롯-아이템 사용' 이 3가지 단계를 구현하기 위한 컴포넌트들을 구현했습니다. 이번에는 탄약, 회복아이템과 같은 가방에 저장할  수 있는 아이템을 위한 컴포넌트를 구현함으로써 유연성 있는 아이템 장착 및 사용 시스템을 구현 해보도록 하겠습니다.
# 기능에 대한 고찰
![](/assets/images/old/a19c3dda-d4ca-44bf-9b26-f8ec11091429-image.png)

저번 글에 해당하는 UI가 오른쪽에 있는 파란색 박스였다면 이번에는 왼쪽 빨간색으로 표시한 곳 안에 있는 UI입니다. 이 공간은 내가 가방에 넣을 수 있는 아이템들을 위한 공간이며, 다양한 아이템들이 이 곳에 저장됩니다. 플레이어는 이 인벤토리를 위해 여러가지 조작을 할 수 있는데, 이는 다음과 같습니다.
- 특정 키 버튼을 눌러 아이템을 습득(아이템과 상호작용)
- 마우스로 아이템을 드래그 하여 바닥(월드)에 드랍
- 아이템을 소분하여 바닥(월드)에 드랍

이 외에도 UI가 완성되었을 때 추가적으로 호출되어야 할 기능은 다음과 같습니다.
- 아이템을 퀵 슬롯에 장착
- 아이템을 사용

또한, 인벤토리는 일반적으로 RPG에서 주로 사용하는 슬롯형 인벤토리와는 다르게, 자동 정렬되는 구조를 사용하기로 결정됐습니다. 따라서 아이템을 드래그하여 다른 칸으로 옮기거나, 인벤토리 내부에서 아이템을 나눌 필요는 없습니다. (자동 정렬, 자동 합치기)


# 구조 설계 및 구현
## Inventory Manager Component
아래 이미지는 저장 가능한 아이템과 상호작용 했을 때의 플로우 차트입니다.
![](/assets/images/old/4b47c04a-4386-43bc-a09c-a2275f8e3c50-image.png)

 FGameplayTag를 Key값으로 하는 Map을 컨테이너로 사용합니다. 가방에 저장될 아이템들의 레퍼런스가 이곳에 저장됩니다. 특이하게도, Map을 사용하는데도 최대 아이템 저장 공간 개수(MaxInventorySize)와 현재 아이템이 차지하고 있는 공간 개수(CurrentItemInInventroyCount)를 관리하고 있는데, 그 이유는 단일 아이템 분류에는 단일 아이템 인스턴스만 가지도록 설계했기 때문입니다. 자세한 내용은 아래에 서술하도록 하겠습니다.
```cpp
protected:
	UPROPERTY(VisibleAnywhere, Category= "Inventory")
	TMap<FGameplayTag, TObjectPtr<UPEStorableItemComponent>> InventoryItems; 

	UPROPERTY(EditAnywhere, Category= "Inventory")
	int32 MaxInventorySize;

	UPROPERTY(VisibleAnywhere, Category= "Inventory")
	int32 CurrentItemInInventroyCount;
	
public:
	void AddItemToInventory(UPEStorableItemComponent* Item);
	void DropItemFromInventoryByTag(const int32 &Count, const FGameplayTag &Tag);
	void ClearInventory();
	UPEStorableItemComponent* GetItemByTag(const FGameplayTag &Tag) const;
	
protected:
	void SortInventory();
	void UpdateCurrentItemCount();
```

단일 아이템 인스턴스 관리를 위해 같은 분류의 아이템과 상호작용 했을 때(e.g. 소총 탄환이 이미 인벤토리에 존재하고, 새로운 소총 탄환 인스턴스와 상호작용 하여 아이템을 습득할 때)는 기존 인스턴스의 개수를 갱신하고, 새로 상호작용한 아이템은 월드에서 제거합니다. 

```cpp
void UPEInventoryManagerComponent::AddItemToInventory(UPEStorableItemComponent* Item)
{
    // 동일한 아이템이 있는 경우 스택 추가
    if (UPEStorableItemComponent* ContainItem = GetItemByTag(ItemTag))
    {
        Item->OnItemPickedUp(); 
        Item->DestroyItem(); // 중복 아이템 제거
        ContainItem->AddItemCount(Item->GetItemCount());
        // ...
    }
    else
    {
        InventoryItems.Add(ItemTag, Item);
        // ...
    }
}
```

인벤토리의 아이템을 필드에 드랍할 때에는 아이템 전체를 버릴 수도 있고, 소분해서 버릴 수도 있습니다. 아래 플로우차트는 해당 기능의 순서를 나타냅니다.
![](/assets/images/old/74ae898b-00d3-47cd-a79c-95ab5e652327-image.png)

실제 아이템이 버려지는 명령은 해당 Item 클래스에서 실행됩니다. 이 함수들은 인터페이스를 통해 정의되어 있으며,  컴포넌트가 호출합니다.

```cpp
void APEItemBase::OnDropToWorld(int32 Count, const FVector& Location, const FRotator& Rotation)
{
	if (Count >= ItemCount)
	{
		OnDropToWorld(Location, Rotation);
	}
	else
	{
		SplitAndDropItem(Count, Location, Rotation);
	}
}

void APEItemBase::SplitAndDropItem(int32 Count, const FVector& Location, const FRotator& Rotation)
{
	// 아이템 개수를 감소시킴
	ItemCount -= Count;
	StackCount = 1 + ((ItemCount - 1) / MaxStackCount);
		
	// 복제된 아이템을 생성
	if (GetWorld())
	{
		APEItemBase* DuplicatedItem = GetWorld()->SpawnActor<APEItemBase>(GetClass(), Location, Rotation);
		if (DuplicatedItem)
		{
			// 복제된 아이템의 속성을 설정
			DuplicatedItem->OnDuplicated( ... );
			DuplicatedItem->OnDropToWorld(Location, Rotation);
				
			UE_LOG(LogTemp, Warning, TEXT("Item duplicated: Original count %d, Duplicated count %d"), ItemCount, Count);
		}
	}
}
```

## Storable Item Component & Item Base Class
```UPEStorableItemComponent```는 Inventroy Manager에 저장될 수 있는 아이템에 부착되어 사용하는 컴포넌트 클래스입니다. 해당 컴포넌트는 ```IPEStorable```이라는 인터페이스와 함께 사용되며, Inventory Manager와 통신하여 이벤트가 호출되면 ItemBase의 실제 동작하는 함수를 호출합니다. 이를 통해 유연성과 확장성을 만족하고, 테스트하기 용이하게 구현할 수 있었습니다.

```cpp
// UPEStorableItemComponent
protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Item")
	TScriptInterface<IPEStorable> ComponentOwnerInterface;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item", meta = (Categories = "Item"))
	FGameplayTag ItemTag;

public:
	FGameplayTag GetItemTag() const { return ItemTag; }
	void SetItemTag(const FGameplayTag& NewTag) { ItemTag = NewTag; }

	void OnItemPickedUp() const;
	void OnItemDropped(const FVector& Location, const FRotator& Rotation) const;
	void OnItemDropped(int32 Count, const FVector& Location, const FRotator& Rotation) const;
	void AddItemCount(int32 Count) const;
	void DestroyItem() const;
	int32 GetItemCount() const;
	int32 GetStackCount() const;
   ```
   
   ```cpp
   //IPEStorable
public:
	virtual void OnPickedUp() = 0;
	virtual void OnDropToWorld(const FVector& Location, const FRotator& Rotation) = 0;
	virtual int32 GetItemCount() const = 0;
	virtual int32 GetItemStackCount() const = 0;
	virtual void AddItemCount(int32 Count) = 0;
	virtual void OnDropToWorld(int32 Count, const FVector& Location, const FRotator& Rotation) = 0;
	virtual void SplitAndDropItem(int32 Count, const FVector& Location, const FRotator& Rotation) = 0;
	virtual void DestoryItem() = 0;
  ```
  
  ```PEItemBase```는 아이템의 전반적인 구현 내용을 정의하고 있습니다. 해당 클래스는 아이템에 관련된 속성을 직접 소유하고 관리해야 하기 때문에, 실제 구현부는 여기에 정의됩니다.
  
  ```cpp
  //PEItemBase
  /* Interact 관련 섹션 */
protected:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	TObjectPtr<UPEInteractableComponent> InteractableComponent;

	UPROPERTY(VisibleAnywhere, Category = "Interaction")
	TObjectPtr<AActor> ItemOwnerActor;
	
public:
	virtual void Interact(AActor* Interactor) override;
	virtual bool IsInteractable() const override;

	/* Storable 관련 섹션 */
protected:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Storage")
	TObjectPtr<UPEStorableItemComponent> StorableItemComponent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Storage")
	int32 MaxStackCount;
	
	int32 ItemCount;
	int32 StackCount; // 아이템의 스택 개수(e.g. 최대 64개까지 스택 가능한 아이템이 90개 있을 경우 StackCount는 2가 됌)

	virtual void OnDuplicated( ... );
public:
	virtual void OnPickedUp() override;
	virtual void OnDropToWorld(const FVector& Location, const FRotator& Rotation) override;
	virtual void OnDropToWorld(int32 Count, const FVector& Location, const FRotator& Rotation) override;
	virtual int32 GetItemCount() const override;
	virtual int32 GetItemStackCount() const override;
	virtual void AddItemCount(int32 Count) override;
	virtual void SplitAndDropItem(int32 Count, const FVector& Location, const FRotator& Rotation) override;
	virtual void DestoryItem() override;
   ```
   
   위에서 말씀드렸다 싶히, 동일한 아이템에 대해서는 단일 인스턴스가 관리하도록 설계했습니다. 저희 게임은 아이템에 인벤토리 시스템은 동일 아이템이라도 일정 수량을 초과할 경우 여러 스택으로 분할하여 각 스택이 하나의 슬롯을 차지하도록 기획했습니다.
예를 들어 소총 탄약의 최대 스택 수가 72발이라면, 160발을 보유할 경우 72, 72, 16 발의 세 개의 스택으로 나뉘며, 총 3개의 인벤토리 슬롯을 점유합니다.
이 기획을 보고 저는 각각의 스택이 다른 인스턴스이며, 관리도 따로 해야할지, 아니면 하나의 인스턴스가 관리해야 할지 고민했습니다. (UI에서는 3개의 아이콘으로 나타나며, 실제로 3개의 아이템이 따로 존재한다고 이해되기 때문) 하지만 아래의 같은 문제가 발생할 수 있다고 판단했기 때문에  단일 인스턴스가 관리하도록 설계했습니다.
- 인스턴스가 여러개일 때, 총합이 최대 스택 이하의 개수임에도 2칸 이상의 칸을 소모하는 문제
- 재장전 시 사용해야 하는 탄약 타입을 탐색해야 하는 문제 등

특히 재장전 시 문제가 많이 발생할 것이라고 생각했습니다. 예를들어
- 탄약 30발을 소모해서 장전하는데 1스택 60개, 1스택 5개가 존재한다면 어떤 인스턴스를 먼저 소모해야할지?
- 하나를 모두 소모한 후에 다음 타입에 맞는 탄약을 탐색할 것인지? 아니면 처음부터 탐색할 때 TArray같은 컨테이너를 생성해서 저장해야 할지? 등 고려할 사항이 너무 많아진다고 판단

따라서, 동일 인스턴스에서 관리하고, 총 몇칸의 인벤토리를 차지하는 지 변수로 관리하다가, 이를 인벤토리 칸 수를 관리하거나 UI에 반영할 때 활용하는 식으로 구현했습니다. 이렇게 하면 하나의 인스턴스여도 APEX 처럼 자동으로 아이템의 갯수와 스택을 관리하고, 인벤토리 UI에서도 여러칸을 차지하는 것 처럼 보여줄 수 있기 때문입니다.

# 테스트
아직 UI가 없기 때문에 테스트용 코드를 사용하여 아이템을 1개씩 버려보겠습니다. 아래는 테스트용 코드입니다.
```cpp
void UPEInventoryManagerComponent::ItemDropTest()
{
	//NOTE: Test용 코드
	if (InventoryItems.Num() == 0)
	{
		UE_LOG(LogPE, Warning, TEXT("No items in inventory to drop!"));
		return;
	}
	FGameplayTag Tag = InventoryItems.begin()->Key;
	DropItemFromInventoryByTag(1, Tag);
}
```
각각의 아이템은 3개씩 스택되어 있으며, Map에 가장 앞에 있는 아이템부터 1개씩 드랍됩니다.

![](/assets/images/old/0a8455d7-641d-4ad9-a519-1c0b76e45cdf-image.webp)

정상작동 하는 모습을 볼 수 있습니다.

# 결론
이로써, 아이템과 상호작용, 사용, 보관하는 기능이 어느 정도 완성되었습니다. 앞으로 갈 길도 멀고 이 코드에서도 개선할 점이 많지만, 단일 책임 원칙이나 인터페이스를 활용한 의존성 분리 같은 부분을 만족시키려고 많이 노력했습니다.

이번 구현에서는 특히 단일 인스턴스를 통한 스택형 아이템 관리 방식을 채택함으로써, 복잡한 로직 없이도 깔끔하게 수량 계산과 슬롯 차지를 조절할 수 있도록 설계했습니다. 이를 통해 재장전과 같은 아이템 소비 로직을 단순화할 수 있었고, 인벤토리 UI에서도 마치 여러 슬롯을 차지하는 것처럼 자연스럽게 표현할 수 있게 되었습니다.

앞으로는 팀원 분들과 함께 다음과 같은 개선 및 확장 방향을 고려하고 있습니다.
- 인벤토리 UI와 실제 데이터 연동
- 드래그 앤 드랍 인터랙션 구현 등

이처럼 인벤토리 시스템은 게임 전반의 UX에 영향을 미치는 중요한 요소인 만큼, 확장성 있고 직관적인 구조를 계속해서 유지하며 개발을 이어갈 예정입니다. 다음 글에서는 전투 시스템에 관한 내용으로 뵙도록 하겠습니다.