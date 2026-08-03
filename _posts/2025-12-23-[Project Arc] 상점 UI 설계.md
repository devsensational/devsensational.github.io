---
title: "[Project Arc] 상점 UI 설계"
description: "오늘은 언리얼 엔진 UMG를 사용해 상점(Shop) UI를 설계·구현한 과정을 정리해 보았습니다. 특히 아이템별 개별 위젯 구성, 구매/판매 가격 분리, 아이템 ID 관리, Vertical List 기반 아이템 나열에 초점을 두고 작업을 진행하였습니다."
date: 2025-12-23T12:01:22.607Z
tags: ["Project ARC","UE5"]
categories: [Project CM + Project Arc]
---
오늘은 언리얼 엔진 UMG를 사용해 상점(Shop) UI를 설계·구현한 과정을 정리해 보았습니다. 특히 **아이템별 개별 위젯 구성**, **구매/판매 가격 분리**, **아이템 ID 관리**, **Vertical List 기반 아이템 나열**에 초점을 두고 작업을 진행하였습니다. 본 문서는 추후 상점 기능을 확장하거나 다른 인벤토리/상점 UI를 설계할 때 참고 자료로 활용하기 위해 작성하였습니다.

---

## 상점 요소 위젯(UCMShopContentElementWidget) 설계

- 목적
  - 상점 리스트에서 **한 개의 아이템**을 표현하는 전용 위젯
  - UI 관점에서 재사용 가능한 단위 컴포넌트로 설계


- 표시 요소
  - 아이템 이미지: `UImage* ItemImage`
  - 아이템 이름: `UTextBlock* ItemNameText`
  - 구매 가격: `UTextBlock* BuyPriceText`
  - 판매 가격: `UTextBlock* SellPriceText`


- 동작 요소 (버튼)
  - 구매 버튼: `UButton* BuyButton`
  - 판매 버튼: `UButton* SellButton`


- 데이터 필드
  - 아이템 아이콘: `TObjectPtr<UTexture2D> ItemIcon`
  - 아이템 이름: `FText ItemName`
  - 구매 가격: `int32 BuyPrice`
  - 판매 가격: `int32 SellPrice`
  - 아이템 식별자: `int32 ItemId` 또는 `FName ItemId` (프로젝트 상황에 맞게 선택)


- 핵심 설정 함수
  - `SetItemDisplayData(UTexture2D* InIcon, const FText& InName, int32 InBuyPrice, int32 InSellPrice, int32 InItemId)`
    - 아이콘, 이름, 구매/판매 가격, 아이템 ID를 한 번에 세팅
    - 내부 Transient 필드에 값 저장 후, 바인딩된 위젯에 텍스트/이미지 반영


- 버튼 활성 제어
  - `SetButtonsEnabled(bool bEnableBuy, bool bEnableSell)`
    - 상황에 따라 구매만 가능 / 판매만 가능 / 둘 다 비활성 등을 제어


- 버튼 클릭 이벤트 처리 흐름
  - `NativeOnInitialized()`에서 버튼 클릭 바인딩
    - `BuyButton->OnClicked.AddDynamic(this, &UCMShopContentElementWidget::HandleBuyClicked);`
    - `SellButton->OnClicked.AddDynamic(this, &UCMShopContentElementWidget::HandleSellClicked);`
  - 내부 핸들러에서 델리게이트 브로드캐스트
    - `OnBuyRequested.Broadcast(this);`
    - `OnSellRequested.Broadcast(this);`
  - 외부(상점 메인 위젯)가 이 델리게이트에 바인딩해 실제 구매/판매 로직을 처리


- 외부에서 참조 가능한 Getter
  - `GetBuyPrice()` / `GetSellPrice()`
  - `GetItemName()` / `GetItemIcon()`
  - `GetItemId()`
  - 상위 위젯이 ElementWidget을 통해 아이템 정보를 재조회할 수 있도록 설계

---

## 상점 데이터 구조(FCMShopItem) 설계

- 목적
  - 상점에 노출할 아이템 정보를 모아 관리하기 위한 구조체
  - 상점 위젯이 `TArray<FCMShopItem>`를 기준으로 리스트를 생성하도록 설계


- 필드 구성
  - `ItemID`: 아이템 고유 식별자 (int32)
  - `BuyPrice`: 구매 가격
  - `SellPrice`: 판매 가격
  - `Quantity`: 수량 (스택 수, 재고 등 다양한 용도로 확장 가능)
  - `ItemName`: UI 표시용 이름
  - `ItemIcon`: UI 표시용 아이콘 텍스처


- 설계 포인트
  - Blueprint에서도 손쉽게 세팅할 수 있도록 `BlueprintType`, `EditAnywhere`, `BlueprintReadWrite`로 설정
  - 실제 게임 데이터(데이터 테이블, 데이터 애셋 등)와 연결하거나, 임시 테스트 데이터로도 사용 가능하게 유연하게 설계


---

## 상점 메인 위젯(UCMShopWidget) 설계

- 역할
  - 전체 상점 화면을 담당하는 메인 컨테이너 위젯
  - `VerticalBox` 안에 여러 `UCMShopContentElementWidget`을 동적으로 생성하여 리스트를 구성


- 주요 멤버
  - `ShopItemListBox`
    - 타입: `UVerticalBox*`
    - 역할: 상점 아이템들을 세로로 나열하는 컨테이너
    - UMG 디자이너에서 `BindWidget` 이름과 동일하게 배치
  - `ShopItemWidgetClass`
    - 타입: `TSubclassOf<UCMShopContentElementWidget>`
    - 역할: 각 아이템 엘리먼트로 생성할 위젯 클래스 (BP 기반으로 지정)
  - `ShopItems`
    - 타입: `TArray<FCMShopItem>`
    - 역할: 실제 상점에 표시할 아이템 데이터 목록


- 초기화 흐름
  - 생성자: `UCMShopWidget(const FObjectInitializer& ObjectInitializer)`
  - `NativeOnInitialized()`에서 초기 리스트 빌드 호출
    - `BuildShopList();`
    - 디자이너에서 `ShopItems`를 미리 세팅해 둔 경우 바로 UI에 리스트가 생성되도록 구성


- 리스트 빌드 로직 (`BuildShopList`)
  - `ShopItemListBox` 또는 `ShopItemWidgetClass`가 유효하지 않으면 조기 리턴
  - 기존 자식 위젯 제거: `ShopItemListBox->ClearChildren();`
  - `ShopItems` 배열을 순회하며 다음 작업 수행
    - `CreateWidget<UCMShopContentElementWidget>(this, ShopItemWidgetClass)`로 엘리먼트 위젯 생성
    - `SetItemDisplayData`로 이미지/이름/구매·판매 가격/ID 설정
    - `OnBuyRequested`, `OnSellRequested` 델리게이트를 메인 위젯의 핸들러에 바인딩
    - `ShopItemListBox->AddChild(ElementWidget)`으로 VerticalBox에 추가
    - `UVerticalBoxSlot`로 캐스팅해 정렬, 패딩 등 레이아웃 세부 설정


- 상점 데이터 갱신 (`SetShopItems`)
  - 외부에서 `TArray<FCMShopItem>`을 넘겨받아 `ShopItems`를 교체
  - 교체 직후 `BuildShopList()` 재호출로 UI를 바로 갱신
  - 코드/블루프린트 어디서든 상점 데이터만 갈아끼우면 UI 전체가 새로 그려지는 구조


- 버튼 클릭 이벤트 최종 처리
  - `HandleElementBuyRequested(UCMShopContentElementWidget* ElementWidget)`
    - `ElementWidget->GetItemId()`와 `GetBuyPrice()`로 어떤 아이템인지, 얼마인지 확인
    - 실제 구매 로직 (골드 차감, 인벤토리 추가 등)과 연결 예정
  - `HandleElementSellRequested(UCMShopContentElementWidget* ElementWidget)`
    - `ElementWidget->GetItemId()`와 `GetSellPrice()`를 사용
    - 실제 판매 로직 (인벤토리에서 제거, 골드 지급 등)과 연결 예정
  - 상점 위젯은 **UI 이벤트를 게임 로직 레이어로 전달하는 허브** 역할을 담당


---

## UMG 에디터에서의 연결 작업 정리

- 상점 메인 위젯 BP (`UCMShopWidget` 기반)
  - 위젯 트리에서 `VerticalBox` 추가 후 이름을 `ShopItemListBox`로 지정
  - 클래스 디폴트에서 `ShopItemWidgetClass`에 `UCMShopContentElementWidget` 기반 BP를 할당
  - 테스트용으로 `ShopItems` 배열에 몇 개의 아이템 데이터 직접 입력해 즉시 미리보기 가능하게 설정


- 상점 요소 위젯 BP (`UCMShopContentElementWidget` 기반)
  - 이미지/텍스트/버튼 위젯 배치 후 이름 매칭
    - `ItemImage`
    - `ItemNameText`
    - `BuyPriceText`
    - `SellPriceText`
    - `BuyButton`
    - `SellButton`
  - C++의 `BindWidgetOptional` 속성과 이름이 일치하도록 관리해 자동 바인딩 확인

---

오늘은 언리얼 엔진 UMG를 사용해 상점 UI를 설계하고, 아이템 단위 위젯과 상점 메인 위젯 사이의 책임을 분리하는 구조를 구현해 보았습니다. 아이템 이미지, 이름, 구매/판매 가격, 그리고 식별용 ID까지 한 번에 관리할 수 있도록 설계함으로써 추후 실제 게임 데이터 및 인벤토리 시스템과의 연동이 훨씬 수월해질 것으로 기대하고 있습니다.

향후에는 오늘 설계한 UI 구조를 기반으로 실제 골드, 인벤토리, 툴팁, 필터링/정렬 기능 등을 추가하여 보다 완성도 높은 상점 시스템으로 확장해 나갈 계획입니다. 오늘의 정리가 이후 작업에 도움이 되기를 바랍니다.

