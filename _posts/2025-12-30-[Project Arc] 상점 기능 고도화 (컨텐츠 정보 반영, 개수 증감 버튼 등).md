---
title: "[Project Arc] 상점 기능 고도화 (컨텐츠 정보 반영, 개수 증감 버튼 등)"
description: "오늘은 프로젝트에서 Shop UI를 구현하고, 특히 상점 리스트에서 아이템을 선택했을 때 상세 패널에 정보가 반영되는 흐름과 아이템 수량(Quantity) 증감 UI를 중심으로 작업을 진행하였습니다."
date: 2025-12-30T11:31:07.733Z
tags: ["project arc","ue5"]
image:
  path: /assets/images/old/7dd659b9-5083-43de-9fd3-bc26c0d3051d-image.webp
categories: [Project CM + Project Arc]
---
오늘은 프로젝트에서 Shop UI를 구현하고, 특히 **상점 리스트에서 아이템을 선택했을 때 상세 패널에 정보가 반영되는 흐름**과 **아이템 수량(Quantity) 증감 UI**를 중심으로 작업을 진행하였습니다. 또한 상점 UI를 여는 과정에서 **PlayerController–NPC–ShopComponent** 사이의 통신 구조를 다시 정리하고, 이를 코드 레벨에서 점검하는 시간을 가졌습니다.

이번 작업의 핵심은 다음과 같습니다. **CMShopContentElementWidget을 클릭 → CMShopWidget에서 선택 상태 갱신 → 상세 UI에 이름/설명/수량 표시 → 수량 버튼으로 Quantity 증감**까지의 흐름을 자연스럽게 만드는 것이었습니다.

---

## 오늘 구현/정리한 내용

### Shop UI 전체 흐름 요약

![](/assets/images/old/69f725e2-b153-4e5f-9e1e-475326017a08-image.png)


- 서버에서 상점 데이터를 가져와서 **클라이언트의 UCMShopWidget**에 전달하는 기존 구조를 재확인하였습니다.
- `CreateShopWidget`에서 이미 상점 위젯 인스턴스가 있을 경우에는 **SetShopItems + BuildShopList**만 다시 호출하여 재사용하도록 되어 있음을 확인했습니다.

---

### CMShopWidget: 아이템 선택 및 수량 표시 로직

#### 주요 멤버 정리

- `FCMShopItemContent CurrentSelectedItem;`
  - 현재 선택된 상점 아이템 정보 구조체
- `int32 SeletedItemQuantity = 0;`
  - 현재 선택된 아이템의 수량(Quantity)
- `UTextBlock* SelectedItemNameText;`
  - 선택 아이템 이름 표시용 텍스트
- `UTextBlock* SelectedItemQuantityText;`
  - 선택 아이템 수량 표시용 텍스트
- `UTextBlock* ItemDescriptionText;`
  - 선택 아이템 설명 표시용 텍스트
- `UButton* AddItemQuantityButton;`
  - 수량 증가 버튼(+)
- `UButton* SubtractItemQuantityButton;`
  - 수량 감소 버튼(-)

#### 초기화 및 버튼 바인딩

- `NativeOnInitialized()`에서 다음과 같이 버튼과 핸들러를 바인딩
  - `AddItemQuantityButton -> OnClickedAddItemQuantityButton`
  - `SubtractItemQuantityButton -> OnClickedSubtractItemQuantityButton`
- 이 핸들러 함수들은 반드시 `UFUNCTION()`으로 선언해 델리게이트와 호환되도록 처리

#### 아이템 선택 처리: HandleElementSelected

`UCMShopContentElementWidget`(리스트 요소)을 클릭했을 때 호출되는 콜백입니다.

- 역할
  - 리스트에서 클릭된 요소의 `FCMShopItemContent`를 받아와 **현재 선택 아이템**으로 저장
  - 선택과 동시에 수량을 **1로 초기화**
  - 상세 UI 텍스트를 갱신

개념적으로는 다음과 같습니다.

- `CurrentSelectedItem = ElementWidget->GetItemContent();`
- `SeletedItemQuantity = 1;`
- `UpdateSelectedItemDisplay();`

#### 상세 표시 함수: UpdateSelectedItemDisplay

선택된 아이템 정보를 실제 UI 텍스트에 반영하는 책임을 가집니다.

- 이름 텍스트
  - `SelectedItemNameText->SetText(...)` 호출
  - `FCMShopItemContent` 내부의 이름 필드 타입을 고려하여 `FName` → `FText::FromName`, 또는 이미 `FText`라면 그대로 세팅
- 수량 텍스트
  - `SelectedItemQuantityText->SetText(FText::AsNumber(SeletedItemQuantity));`
- 설명 텍스트
  - `ItemDescriptionText->SetText(CurrentSelectedItem.ItemDescription);`

에디터에서 바인딩한 텍스트 위젯들이 `nullptr`일 수 있으므로, 각 항목마다 `if (SelectedItemNameText)` 같은 **널 체크 후 세팅**하는 패턴으로 작성했습니다.

#### 수량 증감 로직: UpdateSelectedItemQuantityDelta

수량 버튼 양쪽에서 공통으로 사용하는 내부 함수입니다.

- 인자
  - `int32 Delta` : +1, -1 등의 증감 값
- 처리
  - `SeletedItemQuantity = FMath::Clamp(SeletedItemQuantity + Delta, 1, 99);`
    - 최소 1, 최대 99로 제한
  - `UpdateSelectedItemDisplay();` 호출하여 UI를 동기화

이렇게 함으로써, 수량이 UI와 항상 **동일한 상태**를 유지하게 했습니다.

#### 수량 버튼 클릭 핸들러

- `OnClickedAddItemQuantityButton()`
  - `UpdateSelectedItemQuantityDelta(1);`
- `OnClickedSubtractItemQuantityButton()`
  - `UpdateSelectedItemQuantityDelta(-1);`

버튼은 단순히 **증감 방향만 결정**하고, 실제 로직은 `UpdateSelectedItemQuantityDelta`에 몰아 넣어 중복을 줄였습니다.

![](/assets/images/old/61e6cc62-0935-44ee-a68e-47d355ded6ef-image.png)


---

### CMShopContentElementWidget과 CMShopWidget의 연결 방식

`UCMShopContentElementWidget`은 상점 리스트의 개별 아이템 슬롯입니다. 오늘은 이 위젯이 **어떻게 상위 ShopWidget에 "선택됨"을 알리는지** 흐름을 명확히 이해하는 데 집중했습니다.

#### 데이터 전달 구조 (정리)

- `CMNpcShopComponent`에서 `TArray<FCMShopItemContent>`를 생성 및 관리
- `ACMPlayerController::Server_RequestShopData_Implementation`
  - NPC를 찾고, 그 NPC의 `UCMNpcShopComponent`에서 `GetShopItemContents`로 아이템 배열 획득
  - ListenServer/클라 구분 후, 최종적으로 `CreateShopWidget(ShopItems)` 호출
- `UCMShopWidget::BuildShopList()`
  - `ShopItems`를 순회하면서 `UCMShopContentElementWidget` 인스턴스들을 생성
  - 각 슬롯에 `SetItemDisplayData(Item, this)`와 같은 방식으로
    - 표시용 데이터(이름, 가격, 아이콘 등)
    - 콜백 대상(ShopWidget 자기 자신)을 전달
- `UCMShopContentElementWidget` 내부에서 OnClicked 등 이벤트 발생 시
  - 바인딩된 `UCMShopWidget::HandleElementSelected(this)` 호출

이 과정을 통해 **슬롯 → 상점 메인 위젯**으로 자연스럽게 선택 이벤트가 올라오도록 설계되어 있습니다.

![](/assets/images/old/86e84f1d-6b6f-447f-bf8e-1fd3745587ba-image.png)


---

### 네이밍 및 바인딩 정리 (Count → Quantity)

오늘 도중에 발견한 네이밍 혼선을 정리했습니다. 기존에는 일부 버튼/텍스트가 `Count`라는 이름을 사용하고 있었고, 다른 부분에서는 `Quantity`를 사용하고 있었습니다. 이를 전부 `Quantity`로 통일했습니다.

- 버튼
  - `AddItemCountButton` → `AddItemQuantityButton`
  - `SubtractItemCountButton` → `SubtractItemQuantityButton`
- 텍스트
  - `SelectedItemCountText` → `SelectedItemQuantityText`
- 함수
  - `OnClickedAddItemCountButton` → `OnClickedAddItemQuantityButton`
  - `OnClickedSubtractItemCountButton` → `OnClickedSubtractItemQuantityButton`
- UI 바인딩 주의
  - C++ 이름을 변경한 후, UMG 디자이너에서 **위젯 변수 이름도 동일하게 변경**해야 바인딩이 끊기지 않음을 재확인했습니다.

이 정리 덕분에 코드 가독성과 의도가 보다 명확해졌습니다.

---

## 마치며

오늘은 Shop UI에서 **아이템 선택 → 상세 정보 반영 → 수량 증감**이라는 한 흐름에 집중해서 구현과 리팩터링을 진행하였습니다. 특히 `CMShopContentElementWidget`과 `CMShopWidget` 사이의 이벤트 전달 구조를 확실히 이해하고 정리하면서, 이후 구매/판매 요청(`RequestBuyItem`, `RequestSellItem`)을 구현할 때도 같은 패턴을 확장해서 사용할 수 있겠다는 생각이 들었습니다.

또한, 이름을 `Count`에서 `Quantity`로 통일하고 버튼/텍스트/함수를 일관되게 정리한 덕분에, 나중에 상점 관련 기능을 확장할 때 혼동이 줄어들 것으로 기대합니다. 다음 단계에서는 오늘 만든 선택/수량 정보를 바탕으로 실제 서버 RPC(`Server_RequestBuyItem`, `Server_RequestSellItem`)와 연동하여 아이템 구매/판매 로직을 완성해 볼 계획입니다.
