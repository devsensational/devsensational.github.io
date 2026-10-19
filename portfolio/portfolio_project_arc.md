---
layout: page
title: "Project Arc (Project CM)"
permalink: /portfolio/portfolio_project_arc/
---

## 프로젝트 개요
---

![image.png](/assets/images/portfolio_project_arc_images/image.png)

- **프로젝트 명:** Project Arc (Project CM)
- **역할**
    - GameMode 및 State 구현
    - 로딩 시퀀스 및 클라이언트 동기화 시스템 구현
    - 절차적 맵 생성 구현
    - Tree형 NPC 대화 및 액션(상호작용) 구현
    - 서버 권한 기반 상점(구매/판매 검증 포함) 구현
- **개발 환경**
    - Unreal 5.6.1
    - C++
    - PC/Windows
- **기간:** 2025.10.28 ~ 2026.01.12
- **인원:** 8명

> 프로젝트 중반 기획이 PvPvE → 내러티브 중심 PvE(Listen Server 기반 2인 코옵)로 변경되면서, 절차적 맵 생성은 최종 방향에서 제외되었고 NPC 상호작용·상점 기능은 구현을 마쳤으나 최종 빌드에는 포함되지 않았습니다.

---

## 핵심 기능

### 1. 로비 및 클라이언트 동기화 시스템

> **멀티플레이 로비에서 클라이언트 로딩 시퀀스를 단계별로 제어하고, 네트워크 복제 타이밍으로 인한 접속자 목록 누락·중복 문제를 해결했습니다.**

#### 기술적 포인트

- **클라이언트 로딩 시퀀스 제어 (로딩 3단계 분리)**
    - `ACMGameStateBase`가 동기화 대상(`SyncedComponentMap`, 예: `GameState`)의 준비 완료를 `NotifyComponentSynced`로 집계하고, 모두 준비되면 `OnLoadBegin` → `OnLoadUI` → `OnLoadCompleted` 3단계 순차 로딩 진행
    - 각 단계를 `SetTimerForNextTick`으로 예약 및 브로드캐스트하여 단계 간 실행 순서를 프레임 단위로 분리
    - `DECLARE_MULTICAST_DELEGATE` 기반 C++ 델리게이트를 확장 지점으로 제공하고, 단계 처리 함수(`HandleLoadBegin` 등)를 `virtual`로 열어 하위 GameState가 단계를 추가할 수 있도록 설계
    - 예) 절차적 맵 스테이지용 `ACMGameStateMainStage`: 서버가 정한 `Seed`를 Replicate하고 동기화 조건으로 등록한 뒤, `LoadBegin` → `GenerateMap` → `LoadUI` 순서로 맵 생성 단계를 삽입
- **PlayerState Replicated 변수 동기화 경합 해결 (상세 내용은 트러블 슈팅 1번 항목 참조)**
    - `BeginPlay`와 `OnRep` 간 네트워크 초기화 타이밍 차이로 인한 로비 접속자 리스트 누락/중복 현상 해결
    - `SetTimerForNextTick`을 활용해 `GameState`가 준비되지 않은 경우 처리를 다음 프레임으로 연기
    - `bAddedToLobby` 플래그 도입으로 `REPNOTIFY_Always` 재호출 상황에서도 중복 등록 방지
- **플레이어 세션(입퇴장) 관리**
    - 오버라이드한 `GameState`의 `AddPlayerState` / `RemovePlayerState`가 호출되지 않던 문제(GameStateClass 불일치, 서버 전용 호출, 특수 로그인 흐름 등)를 분석
    - `GameMode`의 `PostLogin` / `Logout`을 오버라이드해 입퇴장 이벤트를 `GameState` 델리게이트로 브로드캐스트하도록 변경

#### 핵심 기여

- 클라이언트 로딩 시퀀스 및 멀티플레이 로비 제어 구조 설계 및 구현
- 네트워크 복제 타이밍에 따른 로비 상태 동기화 문제 해결
- `GameMode` 진입점(`PostLogin` / `Logout`) 기반의 입장/퇴장 이벤트 처리 구조 구축

#### 실행 결과

![로딩 시퀀스 순차 실행](/assets/images/old/bd70a123-80c5-44c4-b779-6563b9b1f387-image.png)
_Sync가 모두 완료된 후 차례대로 Load 메소드를 실행하는 것을 볼 수 있습니다_

![로비 플레이어 리스트 출력](/assets/images/old/c35883c4-fd0f-4213-a6ef-5f5cfab54cc9-image.png)
_본인을 제외한 다른 클라이언트들이 로비 리스트에 정상적으로 출력됩니다_

![입퇴장 호출 검증](/assets/images/old/7e09ef98-acf9-4b3b-a753-49c38cb7c318-image.png)
_서버 로그에서 GameMode PostLogin / Logout을 통해 입장 및 퇴장 이벤트가 호출되는 것을 확인했습니다_

#### 구현 과정

[[Project CM] 클라이언트 동기화를 위한 로딩 시퀀스 구현]({% post_url 2025-10-29-[Project CM] 클라이언트 동기화를 위한 로딩 시퀀스 구현 %})

[[Project CM] PlayerState 추가/제거 함수 문제 발견 및 해결 방안]({% post_url 2025-10-30-[Project CM] PlayerState 추가제거 함수 문제 발견 및 해결 방안 %})

### 2. 시드 기반 **Procedural Map** 생성

![실제 생성된 지형](/assets/images/portfolio_project_arc_images/image%201.png)

>**시드 기반 절차적 맵 생성과 데이터 기반 설정 구조를 통해, 코드 수정 없이 맵 크기·방 구성을 조정할 수 있는 맵 생성 시스템을 설계/구현했습니다.**

#### 기술적 포인트

- **DFS + BFS 조합 구조 설계**
    - 격자 좌표 위에서 랜덤 DFS로 방을 확장해 항상 연결된 스패닝 트리 형태의 방 그래프 생성
    - 시작 방에서 BFS로 각 방까지의 거리를 계산하고, 가장 먼 리프 노드부터 보스 방으로 배치
    - 시작 방·보스 방을 제외한 좌표 중에서 보물 방을 랜덤 선정
    
- **Data-driven 설계 (기획 친화적 구조)**
    
    ![image.png](/assets/images/portfolio_project_arc_images/image%202.png)
    
    - `UCMRoomDataDefinition`에서 맵 크기, 최대 방 개수, 보물/보스 방 개수, 방 타입별 클래스 목록을 설정
    - 맵 생성 알고리즘(`MapGenerateLogicComponent`)과 시작 위치 선택(`SpawnPositionSelectorComponent`)을 컴포넌트로 분리해 교체 가능하도록 구성
- **Actor 기반 월드 구성 자동화**
    - 방 클래스들의 크기(`UCMRoomBoundsBox`)를 측정해 격자 간격을 계산하고, 격자 좌표를 월드 좌표로 변환해 방 액터 스폰
    - 인접 정보에 따라 각 방의 4방향에 Entrance / Wall을 자동 배치
- **재현 가능한 Procedural 시스템 구축**
    - `FRandomStream(Seed)`로 방향 선택·클래스 선택·보물 방 셔플을 수행해, 같은 시드와 데이터로 같은 맵 구조를 재생성
    - `Seed`는 서버의 GameState에서 결정·Replicate하고, 로딩 시퀀스의 동기화 조건으로 묶어 시드 수신 이후에 맵 생성 단계가 실행되도록 구성

#### 핵심 기여

- Procedural Map Generator 구조 설계 및 구현
- Room Graph → World 배치 파이프라인 구축
- 데이터 기반 맵 구성 구조 설계

#### 구현 과정

[[Project Arc] 데이터 기반 Procedural Map Generator + 레벨 스트리밍 구현]({% post_url 2025-11-19-[Project Arc] 데이터 기반 Procedural Map Generator + 레벨 스트리밍 구현 %})

### 3. NPC Dialogue & Action 시스템 구현

>**Tree 기반 Dialogue 구조와 액션 노드를 결합하여, 분기형 대화 중 선택지에 따라 NPC 기능(예: 상점)을 실행하는 컴포넌트 기반 NPC 상호작용 시스템을 설계/구현했습니다.**

![56.gif](/assets/images/portfolio_project_arc_images/56.gif)

![58.gif](/assets/images/portfolio_project_arc_images/58.gif)

#### 기술적 포인트

- **Tree 기반 Dialogue 구조**
    - 대화 노드(`UCMDialoagueNode`, UObject)가 `ParentNode` + `Children` 배열로 트리 구성
    - 선택지는 기본 노드를 상속한 액션 노드(`UCMActionNode`)로 표현하며, 실행할 기능을 `ActionType`(`ECMNpcComponentType`)으로 지정
    - NPC 액터(`ACMNpcBase`)가 `RootDialogueNode` / `AllDialogueNodes`를 UPROPERTY로 보유해 GC 안전성 확보, `LogAllDialogueNodeTexts()`로 전체 트리 순회 디버그
    
- **Dialogue + Action 분리 설계**
    - Dialogue: “무엇을 보여줄 것인가”
    - Action: “무엇을 실행할 것인가”
    - 구조
        - 액션 노드 선택 → `HandleActionByType(ActionType)`
        - `RegisteredComponentMap`에서 해당 타입의 NPC 컴포넌트를 찾아 `PerformAction()` 실행
        - 예시) `ShopComponent` → 상점 UI 요청
    
    → 대화 시스템이 단순 UI가 아닌 **게임 로직 트리거 역할 수행**
    
- **컴포넌트 기반 NPC 확장 구조**
    - `ACMNpcBase` + `UCMNpcComponentBase` 파생 컴포넌트(Dialogue / Quest / Shop)
    - 새 기능은 enum 타입 추가 + 컴포넌트 구현 + 등록만으로 확장하고, 외부 호출부(`HandleActionByType`)는 유지
    
- **블루프린트 기반 대화 트리 구성**
    
    ![image.png](/assets/images/portfolio_project_arc_images/image%203.png)
    
    - `CreateDialogueNode` / `CreateDialogueNodeWithSettings` / `CreateActionNodeWithSettings` API 제공
    - 블루프린트에서 대사 텍스트, 부모 노드, 액션 타입(드롭다운)을 지정해 대화 트리 구성
    
    → C++ 코드 수정 없이 블루프린트에서 대화 내용 구성 가능
    
- **현재 노드 기반 흐름 제어**
    - `CurrentNode`를 기준으로 Next 요청 시 다음 노드로 이동하고 대사를 브로드캐스트 (자식이 없으면 대화 종료)
    - 현재 노드의 자식 중 액션 노드를 찾아 선택지 생성
    - 선택지 선택 시 대화를 종료하고 `HandleActionByType`으로 해당 기능 실행, `CurrentNode`는 루트로 초기화
    
- **UI 자동 생성 및 이벤트 바인딩**
    - 액션 노드 개수만큼 선택지 버튼(`UCMNpcDialogueChoiceElement`) 동적 생성
    - 대화 위젯은 PlayerController의 `UUIManagerComponent` 스택에 Push/Pop
    
    → UI 수정 없이 대화 구조 변경 가능
    
- **이벤트 허브 기반 UI-로직 분리**
    - GameInstanceSubsystem(`UCMLocalEventManager`)의 델리게이트로 NPC ↔ UI 간 이벤트 전달 (다음 노드 요청, 대사 출력, 선택지 생성, 선택 결과)
    - `EndDialogue()`에서 바인딩을 명시적으로 해제해 다음 대화에서의 중복 호출 방지
    
#### 핵심 기여

- Dialogue Tree 구조 설계 및 구현
- Dialogue + Action 분리 아키텍처 설계
- 액션 노드 기반 NPC 컴포넌트 실행 구조 구현
- 블루프린트 기반 대화 트리 구성 API 제공
- GameInstanceSubsystem 이벤트 허브를 통한 UI-로직 분리

#### 구현 과정

[[Project Arc] Tree 구조의 Dialogue 시스템 구현]({% post_url 2025-12-09-[Project Arc] Tree 구조의 Dialogue 시스템 구현 %})

[[Project Arc] NPC Dialogue & Action 시스템 1차 구현 완료]({% post_url 2025-12-12-[Project Arc] NPC Dialogue & Action 시스템 1차 구현 완료 %})

### 4. 서버 권한 기반 Shop 시스템 & 데이터 기반 상점 고도화

![35.gif](/assets/images/portfolio_project_arc_images/35.gif)

> **상점 데이터 조회와 구매/판매 처리를 모두 서버(호스트)에서 수행하고, 클라이언트는 아이템 ID와 수량만 요청하는 서버 권한 기반 상점 시스템을 구현했습니다.**

#### 기술적 포인트

- **서버 권한 기반 상점 데이터 흐름**
    - **구조:**
        - Client → `RequestOpenShopUI(NpcId)` → `Server_RequestShopData` (Server, Reliable, WithValidation)
        - Server → `NpcWorldSubsystem`에서 NPC 조회 → `ShopComponent`의 상점 아이템 목록 획득, 거래 대상 NPC(`CurrentShopNpc`)를 서버에 저장
        - 결과 → Host(리슨 서버)는 바로 위젯 생성, Remote Client는 `Client_ReceiveShopDataAndOpen`으로 전달 후 위젯 생성
    
- **서버 검증 기반 구매/판매 처리**
    - 클라이언트는 `Server_RequestBuyItem` / `Server_RequestSellItem`으로 **아이템 ID와 수량만 전송**하고, 가격은 서버가 보관한 NPC 상점 데이터에서 조회
    - 서버 처리 순서 (구매): 수량 검증 → 상점 아이템 조회 → 총액 계산 → 재화 확인(`CanAfford`) → 재화 차감(`SpendCurrency`) → 인벤토리 지급
    - 인벤토리 공간 부족으로 일부만 지급되면 남은 수량만큼 환불, 전혀 지급되지 않으면 `InventoryFull`로 실패 처리
    - 판매는 판매가 0 이하 아이템 차단 → 인벤토리 차감 성공 시에만 재화 지급
    - `bPurchaseInProgress` 플래그 + `ON_SCOPE_EXIT`로 거래 중 중복 요청 차단 및 어떤 반환 경로에서도 잠금 해제
    - Host는 같은 처리 함수(`PerformBuyItem` / `PerformSellItem`)를 직접 호출하고, Remote Client는 Server RPC를 거치도록 분기
    
    → 클라이언트가 가격·재화를 조작해도 거래 결과에 반영되지 않는 구조
    
- **거래 결과 응답 구조**
    - `FPurchaseResponse`(결과 코드, 아이템 ID, 수량, 총액, 잔액)와 `EPurchaseResult`(Success / InsufficientFunds / InvalidProduct / InvalidQuantity / InventoryFull / ItemNotOwned / ServerError) 정의
    - `Client_ReceivePurchaseResult` → `OnPurchaseResultReceived` 델리게이트 → 상점 위젯에서 결과별 메시지를 색상과 함께 일정 시간 표시
    
- **DataTable 기반 상점 데이터 구조**
    
    ![image.png](/assets/images/portfolio_project_arc_images/image%204.png)
    
    - `FCMShopItemContent`(`FTableRowBase`) 구조체: ItemID / 지급용 `ItemDataAsset` / 구매·판매 가격 / 수량 / 이름 / 아이콘 / 설명
    - `ACMNpcBase`에 `ShopItemDataTable`, `NpcId`를 두고 `BeginPlay`에서 DataTable 행을 읽어 상점 컴포넌트에 주입 → NPC별로 상점 구성을 다르게 지정
    
    → 코드 수정 없이 상점 아이템 추가·변경 가능
    
- **NPC 캐싱 구조 (`UCMNpcWorldSubsystem`)**
    - `TMap<FName, FCMNpcCacheEntry>`(`TWeakObjectPtr<ACMNpcBase>`)에 NPC를 ID 기반으로 캐싱
    - NPC가 `BeginPlay` / `EndPlay`에서 스스로 등록·해제
    
    → 서버에서 `NpcId`만으로 대상 NPC를 바로 조회
    
- **아이템 선택 및 수량 증감 (UX 개선)**
    - 리스트 요소 클릭 → `HandleElementSelected` → 상세 패널에 이름/설명/수량 표시
    - +/- 버튼 기반 수량 조절, 선택 시 1로 초기화 후 `FMath::Clamp`로 1~99 제한, 거래 성공 시 다시 1로 초기화
    - 증감 로직을 `UpdateSelectedItemQuantityDelta` 하나로 모아 버튼 핸들러 중복 제거
    
- **UI 상태 관리**
    - 수량 변경 시 `UpdateSelectedItemDisplay()`를 함께 호출해 내부 상태와 표시 값을 일치시킴
    - 상점을 다시 열 때 기존 위젯을 먼저 Pop한 뒤 새로 Push하여 UI 스택 꼬임 방지
    - `Count` / `Quantity`로 혼용되던 버튼·텍스트·함수 네이밍을 `Quantity`로 통일

#### 핵심 기여

- 서버 권한 기반 상점 데이터 요청·전달 구조 설계 및 구현
- 서버 검증 기반 구매/판매 트랜잭션(재화 확인·차감, 인벤토리 지급, 부분 환불) 구현
- 결과 코드 기반 거래 응답 구조 및 UI 피드백 구현
- DataTable 기반 상점 데이터 관리 구조 설계
- `UCMNpcWorldSubsystem` 기반 NPC ID 캐싱 구조 구현
- 아이템 선택·수량 증감 UI 및 로직 구현

#### 구현 과정

[[Project Arc] 서버 권한 상점 컨텐츠 구성 (UI, 캐싱, Data Table, RPC)]({% post_url 2025-12-26-[Project Arc] 서버 권한 상점 컨텐츠 구성 (UI, 캐싱, Data Table, RPC) %})

[[Project Arc] 상점 기능 고도화 (컨텐츠 정보 반영, 개수 증감 버튼 등)]({% post_url 2025-12-30-[Project Arc] 상점 기능 고도화 (컨텐츠 정보 반영, 개수 증감 버튼 등) %})

---

## 트러블 슈팅

### 1. 멀티플레이 환경의 PlayerState 네트워크 동기화 경합 및 중복 문제 해결

#### 문제 상황
- 로비에서 클라이언트 접속 시, 서버에서 클라이언트로 `PlayerState`의 닉네임(`PendingNickname`)을 동기화하는 과정에서 두 가지 문제가 발생
- **누락 문제:** 접속 타이밍에 따라 로비 접속자 리스트에 플레이어의 닉네임이 등록되지 않음
- **중복 문제:** 동일한 플레이어가 리스트에 여러 번 중복 추가되는 현상 발생

#### 원인 분석
- **네트워크 복제와 월드 초기화의 비동기성 (타이밍 경합):**
    - 언리얼 엔진 네트워크 흐름 상 `PlayerState`의 Replicated 변수들이 클라이언트에 도착하는 시점이 `BeginPlay()`보다 빠르거나 느리다고 보장할 수 없음
    - 변수가 복제되어 `OnRep` 콜백이 호출되더라도, 그 시점에 로비 리스트를 관리하는 `GameState`가 아직 준비되지 않았다면 참조에 실패하여 리스트 추가가 무시됨
- **복제 알림의 재진입:**
    - 클라이언트가 항상 `OnRep`을 받도록 `REPNOTIFY_Always` 옵션을 사용했으나, 이로 인해 값이 동일하더라도 `OnRep`이 다시 호출되며 리스트 추가 로직이 중복으로 실행될 여지가 있었음

#### 해결 방법
**1. SetTimerForNextTick을 활용한 초기화 경합 해결**
- `OnRep` 호출 시 `GameState`의 존재 여부를 먼저 확인
- `GameState`가 아직 준비되지 않았다면 실패 처리하지 않고, `SetTimerForNextTick`으로 **리스트 갱신 로직을 다음 프레임(Tick)에 재시도하도록 연기**

**2. 가드 플래그(bAddedToLobby)를 통한 중복 방지**
- `PlayerState` 내부에 `bAddedToLobby` 상태 플래그를 추가
- 로비 리스트에 이미 추가된 상태라면 조기 종료(Return)하여, `REPNOTIFY_Always`로 인한 `OnRep` 재호출이나 지연 처리 상황에서도 1회만 등록되도록 처리

**3. 초기값 명시로 복제 시점 안정화**
- 서버의 `BeginPlay()`에서 `PendingNickname`의 초기값을 명확하게 세팅하여 복제가 시작되도록 유도

#### 결과

![로비 플레이어 리스트 출력](/assets/images/old/c35883c4-fd0f-4213-a6ef-5f5cfab54cc9-image.png)
_핵심 기능 항목과 동일한 이미지이며, 이해를 돕기 위해 추가했습니다_

- 단일 클라이언트 조인, 다중 클라이언트 동시 조인, `GameState` 지연 생성, `OnRep` 재호출 시나리오에서 유저 목록이 1회씩 등록되는 것을 확인
- 복제 직후 다른 서브시스템과 상호작용해야 하는 로비 환경에서 재사용할 수 있는 초기화 패턴으로 정리

#### 해결 과정

[[Project CM] SetTimerForNextTick을 활용한 PlayerState 동기화 시점 문제 해결]({% post_url 2025-10-31-[Project CM] SetTimerForNextTick을 활용한 PlayerState 동기화 시점 문제 해결 %})

### 2. 맵 생성 시 Entrance 비정상 생성 문제 해결

#### 문제 상황

- Procedural Map 생성 과정에서 **방(Room) 경계에 배치되는 Entrance(문/통로)가 비정상적으로 생성되는 문제 발생**
- 특히:
    - 같은 위치(두 방 사이의 경계)에 Entrance 액터가 **여러 개 겹쳐서 생성됨**
    - 방이 물리적으로 인접해 있음에도 문이 생성되지 않거나, 엉뚱한 방향에 문과 벽이 배치되는 현상 발생

#### 원인 분석

**1. 방향 인덱스 체계 불일치**
- 방 생성 로직(`GenerateRoom`)은 **상/좌/하/우**를 기준으로 동작하나, 벽/문 배치 로직은 **우/하/좌/상**을 기준으로 검사하여 내부적으로 인접 판단이 엇갈림.

**2. 중복 스폰 방지 캐싱 로직의 연산 버그**
- 스폰된 Border 액터를 반대편 방에 공유할 때, 연산자 우선순위 실수(`DirectionIndex + 2 % 4`)로 배열 범위를 벗어난 인덱스에 접근할 수 있었고, 반대편 방에는 반대 방향이 아닌 `DirectionIndex`로 저장하는 인덱스 오류가 있었음.
- 이로 인해 캐싱이 제대로 이루어지지 않아 같은 경계를 처리할 때마다 `SpawnActor`가 다시 호출됨.

**3. 논리적 인접(생성 트리)과 물리적 인접(Grid)의 불일치**
- 트리 형태로 생성된 연결 정보에서는, 실제 격자 좌표상 맞닿아 있더라도 서로 다른 가지(브랜치)에 속한 방이 `ConnectedRooms`에 인접 방으로 담기지 않음.

#### 해결 방법

**1. 전역 방향 인덱스 기준 통일**
- 인접 판단과 벽/문 배치에 쓰이는 `DirectionX/Y`, `DirIndexFromDelta`, `OppositeDir`, `ConnectedRooms[4]`, `RoomBorderActors[4]`, 방향별 EntrancePoint 매핑을 **상/좌/하/우(0~3) 기준으로 통일**하여 로직 간 인접 판단의 일관성 확보.

**2. 공유 리소스(Border) 1회 스폰 및 양방향 캐싱 적용**
- 반대 방향 인덱스를 `(DirectionIndex + 2) % 4`로 수정.
- Entrance 스폰 시, 맞닿은 두 방이 각자의 `RoomBorderActors` 배열에서 동일한 액터 포인터를 참조하도록 수정하여 **A→B, B→A 어느 쪽에서 먼저 접근해도 최초 1회만 스폰되도록 구조 변경**.

**3. FCMRoomPosition 기반 물리적 인접성 재캐싱 (후처리)**
- 모든 방을 스폰한 뒤, DFS 트리의 연결 정보(`Adjacency`)에 의존하지 않고 **최종 격자 좌표(`FCMRoomPosition`)를 기준으로 상/좌/하/우 이웃이 `OutRoomMap`에 있는지 다시 검사**하는 후처리 단계 추가.
- 실제 그리드 상에서 붙어 있는 방들을 `ConnectedRooms`로 양방향 연결하고, Entrance/Wall 배치가 좌표 기반 인접 정보만 참조하도록 변경. 트리 연결 정보는 BFS 거리 계산과 보스 방 선정에만 사용.

#### 결과

![image.png](/assets/images/old/50898fc8-43e3-462e-a6b2-22cee65a5c51-image.png)

| 항목                | 개선 결과                                                         |
| ------------------- | ----------------------------------------------------------------- |
| 다중 스폰/중복 오류 | 경계당 Border 액터를 1회만 스폰하고 양쪽 방이 공유하도록 변경     |
| Entrance 배치 기준  | 트리 연결 정보 대신 격자 좌표(`FCMRoomPosition`) 기반 인접성 사용 |
| 방향 인덱스 체계    | 상/좌/하/우(0~3) 단일 기준으로 통일                               |

#### 해결 과정

[[Project Arc] 맵 생성 시 Entrance 비정상 생성 문제 해결]({% post_url 2025-11-24-[Project Arc] 맵 생성 시 Entrance 비정상 생성 문제 해결 %})

### 3. GameStarter NPC 구현 및 Remote Client 필터링 문제 해결

![57.gif](/assets/images/portfolio_project_arc_images/57.gif)

#### 문제 상황

- NPC와 상호작용(Interact)하면 **서버 인원 전체를 다음 맵으로 이동(Seamless Travel)** 시키는 GameStarter NPC를 구현
- 게임 시작은 **Host(리슨 서버)만** 트리거해야 하지만, Remote Client가 Interact해도 서버에서 GameStarter 로직이 실행될 수 있는 구조였음

#### 원인 분석

**1. 입력 주체와 실행 주체의 분리**

- Interact 입력은 클라이언트에서 발생해 `TryActivateAbilitiesByTag`로 Ability를 요청
- `UCMAbility_Interact`는 `NetExecutionPolicy = ServerOnly`이므로, **누가 입력했든 실제 `Interact` 호출은 항상 서버에서 실행**됨

**2. 서버 실행 여부만으로는 요청 주체를 구분할 수 없음**

- GameStarter 입장에서는 `HasAuthority()` 체크를 통과하더라도, 그 Interact가 Host의 입력인지 Remote Client의 입력인지 알 수 없음
- 결과적으로 Remote Client의 Interact로도 게임 시작이 트리거될 수 있었음

#### 해결 방법

**1. Interactor 기반 Remote Client 필터링**

- Ability 코드는 수정하지 않고, GameStarter NPC의 `Interact_Implementation(AActor* Interactor)` 내부에서 처리
- Interactor → `APawn` → `AController`로 캐스팅 후 `IsPlayerController() && !IsLocalController()`이면 Remote Client가 조종하는 Pawn으로 판별
- Remote Client의 Interact는 `return`으로 무시하고, 허용된 Interactor(Host 등)일 때만 `PerformInteract()` 호출

**2. 연출과 맵 이동의 분리**

- `PerformInteract()`에서 `NetMulticast, Reliable` RPC(`MulticastStartFadeOut`)로 모든 월드에 페이드 아웃 명령 전파
- 각 월드의 로컬 PlayerController에서만 `StartCameraFade`를 실행해 접속자 각자의 화면에 페이드를 적용하고, 열려 있던 UI 스택을 초기화
- `FadeDuration` 타이머 이후 서버에서 `SeamlessTravel(TravelURL)`을 호출해 연출 타이밍과 맵 전환 타이밍을 분리

**변경된 상호작용 Sequence Diagram 보기**

![image.png](/assets/images/portfolio_project_arc_images/image%206.png)

#### 결과

| 항목           | 개선 결과                                                        |
| -------------- | ---------------------------------------------------------------- |
| 게임 시작 권한 | Host의 Interact에서만 게임 시작, Remote Client의 Interact는 무시 |
| 기존 구조 영향 | Interact Ability 구조 변경 없이 NPC 내부에서 필터링              |
| 연출           | 모든 접속자 화면에서 페이드 아웃 후 함께 맵 이동                 |

#### 해결 과정

[[Project Arc] GameStarter NPC 구현 및 Remote Client 필터링 문제 해결]({% post_url 2026-01-06-[Project Arc] GameStarter NPC 구현 및 Remote Client 필터링 문제 해결 %})

<br><br>

<div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
  <a href="/portfolio/" style="display: inline-block; padding: 14px 28px; font-size: 1.05rem; font-weight: 600; color: #495057; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 8px; text-decoration: none; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease-in-out;">
    <i class="fas fa-arrow-left" style="margin-right: 8px; color: #6c757d;"></i> 포트폴리오 리스트로 돌아가기
  </a>
</div>
