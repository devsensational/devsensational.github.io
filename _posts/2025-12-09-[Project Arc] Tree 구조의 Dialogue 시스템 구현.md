---
title: "[Project Arc] Tree 구조의 Dialogue 시스템 구현"
description: "이번 기능에서는 NPC가 단순히 한 줄 대사만 출력하는 수준을 넘어서, 트리 형태로 분기되는 대화 시스템을 직접 설계하고 구현해 보았습니다."
date: 2025-12-09T11:35:04.796Z
tags: ["project arc","ue5"]
image:
  path: /assets/images/old/9c16ca4f-1359-425b-aafd-43c3d0d40c59-image.png
categories: [Project CM + Project Arc]
---
이번 기능에서는 NPC가 단순히 한 줄 대사만 출력하는 수준을 넘어서, **트리 형태로 분기되는 대화 시스템**을 직접 설계하고 구현해 보았습니다. 언리얼 엔진의 `UObject` / `UActorComponent` / `AActor` 구조를 활용해, 블루프린트에서도 직관적으로 편집 가능한 형태를 목표로 했습니다. 특히, "대화를 따라가다 특정 노드에서 액션(상점 열기 등)을 실행"하는 흐름까지 테스트 코드로 구축해 본 것이 핵심입니다.

---

## 전체 구조 개요

- 핵심 타입
  - `ECMNpcComponentType` : NPC 컴포넌트의 종류를 표현하는 enum
  - `UCMDialoagueNode` : 기본 대화 노드(텍스트, 부모/자식 참조 포함)
  - `UCMActionNode` : 기본 노드를 상속받아, 추가로 액션 타입을 가지는 노드
  - `ACMNpcBase` : NPC 액터, 대화 트리 전체를 소유/관리
  - `UCMNpcComponentBase` : NPC용 공통 컴포넌트 베이스
  - `UCMNpcShopComponent` : 예시용 상점 컴포넌트(PerformAction 시 화면 메시지 출력)

- 설계 포인트
  - **대화 노드는 UObject(UCLASS)** 로 구현 → GC 및 블루프린트 호환성 확보
  - **트리 구조**는 `ParentNode` + `Children` 배열로 표현
  - NPC 액터(`ACMNpcBase`)가
    - `RootDialogueNode` (루트 노드)
    - `AllDialogueNodes` (생성된 모든 노드)
    를 UPROPERTY로 보유 → GC에 안전하고, 순회/디버그에 용이
  - 액션 노드는 별도 타입(`UCMActionNode`)으로 구분
    - `ActionType: ECMNpcComponentType`
    - 트리 순회 중 액션 노드를 만나면 `HandleActionByType` 호출

---

## ECMNpcComponentType: 블루프린트에서 쓰는 컴포넌트 타입 enum
```cpp
UENUM(BlueprintType)
enum class ECMNpcComponentType: uint8
{
	Default UMETA(DisplayName = "Default"),
	DialogueComponent UMETA(DisplayName = "Dialogue Component"),
	QuestComponent UMETA(DisplayName = "Quest Component"),
	ShopComponent UMETA(DisplayName = "Shop Component"),
};
```


- 역할
  - NPC에 붙는 컴포넌트의 종류(대화, 퀘스트, 상점 등)를 식별하기 위한 enum
  - `ACMNpcBase`의 `RegisteredComponentMap` 키로 사용
  - `UCMActionNode`의 `ActionType`에도 사용 → 트리 상에서 어느 컴포넌트를 실행할지 지정


- 선언 방식
  - 언리얼 리플렉션 + 블루프린트 노출을 위해 `UENUM(BlueprintType)` 사용
  - 기본형은 `int` (언더라이잉 타입 명시 생략)으로 유지

---

## UCMDialoagueNode: 기본 대화 노드 설계

- 타입
  - `UCLASS(BlueprintType) class UCMDialoagueNode : public UObject`

```cpp
UCLASS(BlueprintType)
class UCMDialoagueNode : public UObject
{
	GENERATED_BODY()

public:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Dialogue")
	TObjectPtr<UCMDialoagueNode> ParentNode = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue")
	TArray<TObjectPtr<UCMDialoagueNode>> Children;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue")
	FText DialogueText;
};
```


- 주요 필드
  - `ParentNode : UCMDialoagueNode*`
    - UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    - 상위 노드 참조 (루트의 경우 nullptr)
  - `Children : TArray<UCMDialoagueNode*>`
    - UPROPERTY(EditAnywhere, BlueprintReadWrite)
    - 자식 노드들(다중 분기 지원)
  - `DialogueText : FText`
    - UPROPERTY(EditAnywhere, BlueprintReadWrite)
    - 실제로 화면/UI에 보여줄 대사 텍스트

- 특징
  - UObject 기반이라 **언리얼 GC 관리 대상**
  - 블루프린트에서
    - 노드의 텍스트를 수정
    - Parent/Children를 직접 연결하여 트리 구성 가능

---

## UCMActionNode: 액션을 수행하는 특수 대화 노드

- 타입
  - `UCLASS(BlueprintType) class UCMActionNode : public UCMDialoagueNode`

```cpp
UCLASS(BlueprintType)
class UCMActionNode : public UCMDialoagueNode
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue")
	ECMNpcComponentType ActionType;
};
```

- 추가 필드
  - `ActionType : ECMNpcComponentType`
    - UPROPERTY(EditAnywhere, BlueprintReadWrite)
    - 이 노드에 도달했을 때 어떤 타입의 NPC 컴포넌트를 실행할지 지정

- 동작
  - 트리 순회 중 `UCMActionNode`로 캐스팅에 성공하면
    - `ActionType` 값을 읽어
    - `ACMNpcBase::HandleActionByType(ActionType)` 호출
  - 예: `ShopComponent` → 상점 열기 컴포넌트의 `PerformAction` 호출

---

## ACMNpcBase: NPC 액터와 대화 트리 관리

- 타입
  - `class ACMNpcBase : public AActor, public ICMNpcHandler`

- 주요 프로퍼티
  - `RootDialogueNode : UCMDialoagueNode*`
    - 대화 트리의 루트 노드
  - `AllDialogueNodes : TArray<UCMDialoagueNode*>`
    - 생성된 모든 대화 노드 모음 (GC + 디버그용)
  - `CurrentNode : UCMDialoagueNode*`
    - 런타임에 현재 플레이어가 위치한 노드(향후 사용 예정)
  - `NpcComponents : TArray<TSubclassOf<UCMNpcComponentBase>>`
    - 에디터에서 지정하는 NPC용 컴포넌트 클래스 목록
  - `ActiveNpcComponents : TArray<UCMNpcComponentBase*>`
    - BeginPlay에서 실제 인스턴스로 생성 후 보관
  - `RegisteredComponentMap : TMap<ECMNpcComponentType, UCMNpcComponentBase*>`
    - 각 컴포넌트 타입에 해당하는 인스턴스를 등록/맵핑

- BeginPlay 흐름
  - `RegisteredComponentMap.Empty()` : 초기화
  - `NpcComponents`를 순회하며
    - `NewObject<UCMNpcComponentBase>(this, ComponentClass)` 로 생성
    - `RegisterComponent()` 호출 → 언리얼 라이프사이클에 등록
    - `ActiveNpcComponents`에 추가
  - 생성된 각 컴포넌트는 자기 `BeginPlay`에서
    - 핸들러(`ACMNpcBase`)에 `RegisterComponent`를 호출하여 스스로 등록
  - 마지막에 테스트용:
    - `FTimerHandle`을 사용해 BeginPlay + 1초 후 `LogAllDialogueNodeTexts()` 실행

---

## 노드 생성 함수 설계 (ACMNpcBase)

### CreateDialogueNode

- 시그니처
  - `UCMDialoagueNode* CreateDialogueNode(TSubclassOf<UCMDialoagueNode> NodeClass, const FText& InDialogueText);`

- 역할
  - 특정 `NodeClass` (기본은 `UCMDialoagueNode`)로 새 노드를 생성하고 텍스트 설정
  - `AllDialogueNodes` 배열에 추가
  - 첫 번째 생성 노드는 자동으로 `RootDialogueNode`로 설정

- 동작 요약
  - `if (!*NodeClass) NodeClass = UCMDialoagueNode::StaticClass();`
  - `NewObject<UCMDialoagueNode>(this, NodeClass)`
  - `NewNode->DialogueText = InDialogueText;`
  - `AllDialogueNodes.Add(NewNode);`
  - `RootDialogueNode`가 비어 있으면 첫 노드를 루트로 등록

### CreateDialogueNodeWithSettings

- 시그니처
  - `UCMDialoagueNode* CreateDialogueNodeWithSettings(TSubclassOf<UCMDialoagueNode> NodeClass, UCMDialoagueNode* Parent, const FText& InDialogueText);`

- 역할
  - `CreateDialogueNode`를 호출해 노드를 생성하고
  - 부모/자식 관계를 동시에 설정하는 편의 함수

- 연결 로직
  - `NewNode->ParentNode = Parent;`
  - `Parent->Children.Add(NewNode);`

### CreateActionNodeWithSettings

- 시그니처
  - `UCMDialoagueNode* CreateActionNodeWithSettings(TSubclassOf<UCMActionNode> NodeClass, UCMDialoagueNode* Parent, const FText& InDialogueText, ECMNpcComponentType InActionType);`

- 역할
  - `UCMActionNode` 타입으로 노드를 생성
  - `DialogueText` + `ActionType` + 부모/자식 관계를 한 번에 설정

- 동작 요약
  - `if (!*NodeClass) NodeClass = UCMActionNode::StaticClass();`
  - `NewObject<UCMActionNode>(this, NodeClass)` 로 액션 노드 생성
  - `NewNode->DialogueText = InDialogueText;`
  - `NewNode->ActionType = InActionType;`
  - `Parent`가 있으면
    - `NewNode->ParentNode = Parent;`
    - `Parent->Children.Add(NewNode);`

- 블루프린트 사용성
  - `InActionType`가 `ECMNpcComponentType` 이라 BP 노드에서 드롭다운으로 선택 가능
  - BP에서 함수를 배치할 때, 트리 상에 어떤 액션을 둘지 직관적으로 설정 가능

---

## 블루프린트에서의 사용 패턴

![](/assets/images/old/9c16ca4f-1359-425b-aafd-43c3d0d40c59-image.png)

- 기본 대화 노드 생성
  - `CreateDialogueNode(UCMDialoagueNode, "대사 텍스트")`
  - 또는 `CreateDialogueNodeWithSettings(UCMDialoagueNode, ParentNode, "텍스트")`

- 액션 노드 생성
  - `CreateActionNodeWithSettings(UCMActionNode, ParentNode, "텍스트", ECMNpcComponentType::ShopComponent)`
  - 분기 지점에 여러 액션 노드를 붙여서 다양한 상호작용 표현


- 트리 테스트
  - NPC 스폰 → BeginPlay 후 1초 뒤
  - `LogAllDialogueNodeTexts()` 자동 호출
  - Output Log에서
    - 각 노드 텍스트
    - 어떤 액션 타입이 처리되었는지 로그
  - 화면(OnScreenDebug)에서는 상점 액션 등 실제 PerformAction의 효과 확인 가능


![](/assets/images/old/16dd127c-cf1c-4c15-8efa-863eace0d4b0-image.png)

---

## 결론

이번 NPC Dialogue 시스템 구현에서는 단순한 대사 나열을 넘어서, **트리 구조와 액션 노드를 결합한 대화 흐름**을 구축해 보았습니다. 대화 노드를 `UObject`로 분리하고, NPC 액터가 트리 전체를 관리하도록 설계함으로써 재사용성과 확장성을 높이고자 하였습니다. 또한, 블루프린트에서 노드를 생성하고 텍스트/액션 타입을 직관적으로 지정할 수 있도록 API를 정리한 덕분에, 디자이너 입장에서의 사용성도 어느 정도 확보할 수 있었습니다.

앞으로는 이 구조를 기반으로 실제 게임 플레이에 필요한 UI 연동, 선택지 표시, 조건부 분기(퀘스트 진행도, 인벤토리 상태 등)에 따른 동적 트리 탐색 등을 추가해 볼 예정입니다. 이번 작업을 통해 언리얼 엔진의 UObject/Actor/Component 구조와 블루프린트 연동 방식에 대한 이해를 한층 더 깊게 할 수 있었던 의미 있는 경험이었습니다.

