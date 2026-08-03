---
title: "[Project Arc] 서버 권한 상점 컨텐츠 구성 (UI, 캐싱, Data Table, RPC)"
description: "오늘은 프로젝트에 NPC 상점 시스템을 구현하고, NpcWorldSubsystem / NpcShopComponent / PlayerController / Shop UI 위젯 사이의 흐름을 점검하는 작업을 진행하였습니다."
date: 2025-12-26T16:26:38.250Z
tags: ["project arc","ue5"]
image:
  path: /assets/images/old/94459a85-c765-4c68-9c1f-407b6d43be98-image.webp
categories: [Project CM + Project Arc]
---
![](/assets/images/old/94459a85-c765-4c68-9c1f-407b6d43be98-image.webp)

오늘은 프로젝트에 NPC 상점 시스템을 구현하고, `NpcWorldSubsystem` / `NpcShopComponent` / `PlayerController` / `Shop UI 위젯` 사이의 흐름을 점검하는 작업을 진행하였습니다. 

---

## 상점 UI 생성 전체 플로우

![](/assets/images/old/b91a9b3b-b47b-4962-aca5-9d561293766e-image.png)

---

## 오늘 작업한 내용 정리

- **데이터 구조 정리**
  - `FCMShopItemContent`
    - `FName ItemID` : 아이템 식별용 ID
    - `int32 BuyPrice` : 구매 가격
    - `int32 SellPrice` : 판매 가격
    - `int32 Quantity` : 수량 정보
    - `FText ItemName` : 표시용 이름
    - `UTexture2D* ItemIcon` : 아이콘 이미지
  - `UDataTable` 기반으로 상점 아이템 목록을 관리하도록 설계
  - `ACMNpcBase` 에 `TObjectPtr<UDataTable> ShopItemDataTable`, `FName NpcId` 를 추가하여 NPC 단위로 상점 구성을 다르게 가져갈 수 있도록 준비

![](/assets/images/old/b265611c-e526-441c-9e23-14cc5122dbb4-image.png)

- **NPC 캐싱 구조 설계 (`UCMNpcWorldSubsystem`)**
  - `FCMNpcCacheEntry`
    - `FName NpcId`
    - `TWeakObjectPtr<ACMNpcBase> NpcActor`
  - `TMap<FName, FCMNpcCacheEntry> NpcCacheMap` 에 NPC를 ID 기반으로 캐싱
  - `RegisterNpc(const FName& NpcId, ACMNpcBase* NpcActor)`
    - `NpcCacheMap.FindOrAdd(NpcId)` 를 이용해 캐시 엔트리 생성/조회 후 값 설정
  - `UnregisterNpc(const FName& NpcId)`
    - NPC가 사라질 때 캐시에서 정리
  - `GetNpcById(const FName& NpcId) const`
    - 캐시에서 ID로 액터를 조회
  - `GetAllNpcEntries(TArray<FCMNpcCacheEntry>& OutEntries) const`
    - 디버깅 및 툴 제작용 전체 조회 함수 제공

- **NPC에서 Subsystem 등록 흐름**
  - `ACMNpcBase`
    - `FName NpcId` 를 에디터에서 설정 가능하도록 노출
    - NPC가 BeginPlay 시점에 `UCMNpcWorldSubsystem` 을 가져와 `RegisterNpc(NpcId, this)` 를 호출하도록 구현
    - EndPlay 시점에는 `UnregisterNpc(NpcId)` 로 정리
  - 이를 통해 서버(호스트)에서 모든 NPC를 ID로 빠르게 찾을 수 있는 구조 확보

- **NPC 상점 컴포넌트 (`UCMNpcShopComponent`)**
  - `UCMNpcComponentBase` 를 상속
  - `TArray<FCMShopItemContent> ShopItemContents` 를 내부에 보관
  - 인터페이스
    - `virtual void PerformAction() override;`
    - `void SetShopItemContents(const TArray<FCMShopItemContent>& InItems);`
    - `void GetShopItemContents(TArray<FCMShopItemContent>& OutItems) const;`
  - `PerformAction()` 에서의 역할
    - NPC 오너(`ACMNpcBase`) 로부터 `NpcId` 를 가져옴
    - 로컬 플레이어 컨트롤러(`ACMPlayerController`)를 찾아 `RequestOpenShopUI(NpcId)` 호출
    - 상점 액션이 트리거되면 컨트롤러를 통해 상점 UI 요청이 이어지도록 연결

- **PlayerController의 상점 UI 흐름 (`ACMPlayerController`)**
  - 프로퍼티
    - `TSubclassOf<UCMShopWidget> ShopWidgetClass;` : 에디터에서 상점 메인 위젯 클래스 지정
    - `UCMShopWidget* ShopWidgetInstance;` : 런타임 인스턴스 보관
  - 상점 UI 요청 진입점
    - `UFUNCTION(BlueprintCallable, Category = "Shop|UI") void RequestOpenShopUI(const FName& NpcId);`
    - 로컬 컨트롤러인지 확인 후 `Server_RequestShopData(NpcId)` 호출
  - 서버 RPC
    - `UFUNCTION(Server, Reliable, WithValidation) void Server_RequestShopData(const FName& NpcId);`
    - 구현부에서
      - `UCMNpcWorldSubsystem` 에서 `GetNpcById(NpcId)` 로 NPC 조회
      - NPC의 `UCMNpcShopComponent` 를 찾아 `GetShopItemContents()` 로 상점 아이템 배열 획득
      - **Host(리슨 서버)** 인 경우: `CreateShopWidget(ShopItems)` 를 바로 호출하여 서버/클라 겸용 컨트롤러에서 UI 생성
      - **순수 클라이언트** 인 경우: `Client_ReceiveShopDataAndOpen(ShopItems)` 클라 RPC 호출
  - 클라 RPC
    - `UFUNCTION(Client, Reliable) void Client_ReceiveShopDataAndOpen(const TArray<FCMShopItemContent>& ShopItems);`
    - 구현부에서 `CreateShopWidget(ShopItems);` 호출
  - 실제 UI 생성 함수
    - `void CreateShopWidget(const TArray<FCMShopItemContent>& InShopItems);`
    - `IsLocalController()` 확인 후
      - 이미 인스턴스가 있으면 `SetShopItems()` / `BuildShopList()` 만 호출하여 갱신
      - 없으면 `UIManagerComponent->PushWidget(ShopWidgetClass)` 로 위젯을 스택에 올린 뒤, 데이터 주입 및 리스트 빌드

- **Shop 위젯 구현 (`UCMShopWidget`)**
  - 구성 요소
    - `UVerticalBox* ShopItemListBox;` (BindWidget)
    - `TSubclassOf<UCMShopContentElementWidget> ShopItemWidgetClass;`
    - `TArray<FCMShopItemContent> ShopItems;`
  - 인터페이스
    - `void SetShopItems(const TArray<FCMShopItemContent>& InItems);`
    - `void BuildShopList();`
  - `BuildShopList()` 동작 개요
    - 기존 자식 위젯 제거
    - `ShopItems`를 순회하면서 `ShopItemWidgetClass` 로 `UCMShopContentElementWidget` 생성
    - 각 엘리먼트에
      - 아이템 이미지, 이름, 구매가, 판매가, 수량 등의 데이터를 바인딩
      - 구매 버튼 / 판매 버튼 클릭 델리게이트를 바인딩하여 상위 위젯 (`UCMShopWidget`) 의 `HandleElementBuyRequested`, `HandleElementSellRequested` 와 연결

- **개별 상점 아이템 위젯 (`UCMShopContentElementWidget`)**
  - 역할
    - 한 개의 `FCMShopItemContent` 를 시각화
    - 이미지, 이름, 가격(구매/판매), 수량 등을 표시
    - "구매" 버튼 / "판매" 버튼 UI 제공
  - 이벤트
    - 구매 버튼 클릭 → 상위 위젯으로 "이 아이템을 구매하고 싶다" 이벤트 전파
    - 판매 버튼 클릭 → 상위 위젯으로 "이 아이템을 판매하고 싶다" 이벤트 전파
  - 상위 위젯에서 실제 로직(인벤토리 차감, 골드 변경, 서버 검증 등)을 처리할 수 있도록 설계

- **Host(리슨 서버) / 클라이언트 동작 차이 정리**
  - 공통
    - `UCMNpcShopComponent::PerformAction()` → `ACMPlayerController::RequestOpenShopUI(NpcId)` 호출
  - Host (ListenServer)
    - `RequestOpenShopUI` → `Server_RequestShopData` 가 같은 프로세스의 서버 컨텍스트에서 실행
    - 서버 내부에서 `NpcWorldSubsystem` 으로 상점 데이터 조회 후 `CreateShopWidget` 을 직접 호출
    - 별도의 클라 RPC 없이도 Host 화면에 상점 UI 표시
  - 순수 클라이언트
    - `RequestOpenShopUI` → Server RPC 로 서버에 상점 데이터 요청
    - 서버에서 상점 데이터 구성 후 `Client_ReceiveShopDataAndOpen` 으로 돌려줌
    - 클라이언트에서 `CreateShopWidget` 을 호출해 UIManager로 Push

- **디버깅용 로그 추가**
  - `CreateShopWidget`
    - 인자로 전달된 `ShopItems.Num()` 과 첫 번째 아이템의 `ItemID`, `ItemName`, `BuyPrice`, `SellPrice`, `Quantity` 를 로그로 출력
    - 서버에서 받은 상점 데이터가 실제로 클라이언트까지 전달되었는지 확인하는 데 사용
  - `Server_RequestShopData`
    - `NpcId` 와 NPC/ShopComponent 유효성 체크 로그 출력
  - `UCMNpcShopComponent::PerformAction`
    - PerformAction 이 실제로 호출되는지, Owner NPC 및 `NpcId` 가 유효한지 확인하는 로그 출력

---

## 마치며

오늘은 NPC 상점 시스템의 전체 흐름을 정리하고, 특히 `NpcWorldSubsystem` 기반의 NPC 캐싱과 `UCMNpcShopComponent` → `ACMPlayerController` → `UCMShopWidget` 으로 이어지는 상점 UI 생성 파이프라인을 점검하였습니다. Host(리슨 서버) 환경과 순수 클라이언트 환경에서의 동작 차이를 고려하여 Server RPC 및 Client RPC 분기를 설계한 덕분에, 네트워크 환경에 따라 상점 UI가 일관되게 동작하도록 만들 수 있었습니다. 앞으로는 이 구조 위에 실제 구매/판매 서버 검증 로직과 인벤토리, 골드 연동 로직을 추가하여 완성도 높은 상점 시스템으로 발전시켜 나가고자 합니다.

