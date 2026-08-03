---
title: "[Project Arc] 데이터 기반 Procedural Map Generator + 레벨 스트리밍 구현"
description: "이번 글에서는 구현한 자동 맵 생성(MapGenerate) 로직과, 생성된 맵 구조에 맞춰 서브 레벨을 동적으로 로드하는 레벨 스트리밍 구조를 정리해 보겠습니다."
date: 2025-11-19T09:59:10.876Z
tags: ["Project ARC","UE5"]
thumbnail: /assets/images/old/3a5351f0-1a0a-4867-b5c2-57866de3efc0-image.png
categories: [Project CM + Project Arc]
---
이번 글에서는 구현한 자동 맵 생성(MapGenerate) 로직과, 생성된 맵 구조에 맞춰 서브 레벨을 동적으로 로드하는 레벨 스트리밍 구조를 정리해 보겠습니다. 특히 어떤 알고리즘으로 방(Room) 그래프를 만들었는지, 그 그래프를 어떻게 실제 월드 좌표에 배치했는지, 그리고 `ACMRoom`과 스트리밍 레벨을 어떻게 연결했는지 위주로 기술해 보겠습니다.

---
## 초기 데이터 설정
![](/assets/images/old/3a5351f0-1a0a-4867-b5c2-57866de3efc0-image.png)

데이터 설정은 ```UCMRoomDataDefinition```을 기반으로 결정됩니다. 이 곳에서 넓이, 방의 갯수, 방 종류 등을 셋팅합니다. 또한, 맵 생성 알고리즘과 시작 지점 선택 알고리즘도 컴포넌트화시켜 기획 담당자가 쉽게 변경할 수 있도록 설계했습니다.

---

## 맵 생성 전반 구조

- 맵 생성의 진입점
  - `UCMMapGenerateLogicBaseComponent::ExecuteMapGenerationLogic`
  - 입력
    - 시드 값 `InSeed`
    - 맵 정의 데이터 `UCMRoomDataDefinition* InMapData`
    - 결과를 담을 `TMap<FCMRoomPosition, TObjectPtr<ACMRoom>>& OutRoomMap`
  - 내부 흐름
    - `GenerateRoom`에서 방 그래프 및 방 액터 생성
    - `PlaceWallsAndEntrances`에서 각 방의 벽과 입구(Entrance) 스폰

- 핵심 데이터 구조
  - `FCMRoomPosition`
    - 정수 좌표 (X, Y)로 방의 격자 상 위치 표현
  - `OutRoomMap`
    - `FCMRoomPosition` → `ACMRoom*` 매핑
    - 맵 생성 알고리즘과 실제 액터 스폰을 연결하는 브리지 역할

---

## 방 그래프 생성 알고리즘 개요

### 1. 사용한 알고리즘

- 전체 알고리즘 성격
  - 격자 기반 그래프 위에서 **랜덤 DFS(깊이 우선 탐색)** 를 이용해 스패닝 트리 형태의 맵을 만듭니다
  - 시작점에서 멀리 떨어진 리프 노드를 보스 방으로, 그 외 후보에서 보물 방을 선정하는 구조

- 주요 의도
  - 항상 **연결 그래프**를 유지해 플레이어가 어디서든 막히지 않고 진행 가능
  - 랜덤 시드를 사용해 **재현 가능한(random but reproducible)** 맵 구조 생성
  - 시작 방에서 거리가 먼 리프에 보스를 배치해 자연스러운 진행 경로 유도

### 2. 좌표계 및 경계 설정

- 맵 크기 정의
  - `UCMRoomDataDefinition`에 너비/높이/최대 방 수, 보물 방 수, 보스 방 수를 정의
- 중심 기준 경계 계산
  - 맵의 중심을 (0, 0)으로 두고
  - X, Y 축에 대해 `MinX, MaxX, MinY, MaxY` 계산
  - 생성 중인 방 위치가 이 범위를 벗어나지 않도록 검사

### 3. DFS 기반 방 확장

- 시작점 설정
  - `Start = FCMRoomPosition(0, 0)`
  - `OutRoomMap.Add(Start, nullptr)`로 먼저 좌표만 점유
  - DFS 스택에 시작 노드를 push

- 방향 정의
  - 인덱스 0~3에 상, 좌, 하, 우를 고정 매핑
  - `DirOffset[4]` 배열을 사용해 `FCMRoomPosition` 델타 계산

- 확장 로직
  - DFS 스택의 top을 현재 노드로 사용
  - 상하좌우 중 아직 점유되지 않았고, 맵 경계 안에 있는 방향만 후보에 추가
  - `FRandomStream`(시드 고정 랜덤)으로 후보 방향 중 하나를 선택
  - 다음 좌표 `Next`를 계산하고, `OutRoomMap.Add(Next, nullptr)`로 점유
  - 인접성 정보 `Adjacency`에 `Curr <-> Next` 양방향으로 추가
  - 부모 방향 정보 `ParentDirIndex`를 기록해 나중에 트리 구조 복원에 사용
  - 더 이상 확장할 방향이 없으면 DFS 스택 pop으로 백트래킹

- 결과
  - `OutRoomMap.Keys()`가 전체 방 좌표 집합
  - `Adjacency`가 그래프의 엣지 집합
  - 구조적으로 **사이클이 거의 없는 트리 또는 트리 기반 그래프**가 형성

### 4. 거리 계산과 리프 노드 분석

- 거리 계산
  - 시작점에서 BFS를 돌며 각 방까지의 최단 거리 `Distance` 계산
  - `Adjacency`를 그대로 사용해 그래프 탐색

- 리프 노드 추출
  - 각 좌표에 대해 인접 방 개수(차수)가 1인 노드를 리프로 간주
  - 시작점(0, 0)은 예외로 처리

- 거리 기반 정렬
  - 리프 리스트를 `Distance` 내림차순으로 정렬
  - 시작점에서 **멀리 떨어진 리프일수록 우선순위가 높음**

- 보스/보물 방 배치
  - 보스 방
    - 정렬된 리프들 중 앞에서부터 `DesiredBoss` 개수만큼 선택
    - `BossPositions` 집합에 좌표 저장
  - 보물 방
    - 시작점과 보스 방을 제외한 모든 좌표를 후보로 수집
    - 랜덤 셔플 후 상위 `DesiredTreasure`개를 `TreasurePositions` 집합으로 선택

---

## 방 액터 스폰과 월드 좌표 매핑

### 1. 방 크기 측정과 간격 계산

- 방 크기 측정 방법
  - `ACMRoom`은 `UCMRoomBoundsBox` 컴포넌트를 통해 실제 방의 월드 상 가로, 세로 크기를 노출
  - `GetRoomWidth`, `GetRoomHeight`에서 박스 익스텐트를 2배한 값으로 길이 산출

- 대표 간격 계산
  - 몬스터/보물/보스 방 클래스들의 CDO를 순회해 최대 폭/높이 측정
  - 값이 너무 작거나 0일 경우, 실제 방을 임시 스폰해 한 번 더 측정
  - 최종적으로 X, Y 방향 `SpacingX`, `SpacingY`를 결정

- 좌표 → 월드 위치 매핑
  - `FVector Location(Pos.X * SpacingX, Pos.Y * SpacingY, 0.f)`
  - 격자 좌표를 그대로 월드 좌표에 선형 변환
  - 방들 사이에 겹침 없이 일정 간격을 확보하는 구조

### 2. 방 타입에 따른 클래스 선택

- 룸 타입 판정
  - 좌표가 `BossPositions`에 포함되면 보스 방
  - 그 외 `TreasurePositions`에 포함되면 보물 방
  - 둘 다 아니면 일반 몬스터 방

- 클래스 선택 로직
  - `UCMRoomDataDefinition`에 각 타입별 클래스 배열 보유
  - `FRandomStream`으로 해당 배열에서 하나를 랜덤 선택
  - 타입별 클래스가 비어 있으면 몬스터 방 클래스로 폴백

- 스폰
  - `World->SpawnActor<ACMRoom>(ClassToSpawn, Location, Rotation, SpawnParams)`
  - 성공 시 `OutRoomMap[Pos]`를 실제 포인터로 덮어써서 좌표와 액터 인스턴스를 연결

---

## 방 간 연결 정보와 입구/벽 배치

### 1. 연결 방향 인덱스 계산

- `DirIndexFromDelta(DX, DY)`
  - 두 좌표 차이(델타)를 상/좌/하/우 인덱스로 변환
  - 예시
    - (0, +1) → 0 (Up)
    - (-1, 0) → 1 (Left)
    - (0, -1) → 2 (Down)
    - (+1, 0) → 3 (Right)

- `OppositeDir(Dir)`
  - 상↔하, 좌↔우로 대응되는 반대 방향 인덱스를 반환

### 2. 연결 바인딩

- 맵 생성 후, 모든 방에 대해 인접 좌표 리스트를 순회
- 인접 좌표에 해당하는 `ACMRoom*`를 찾아 상호 연결
  - `Room->SetConnectedRoom(Dir, NeighborRoom)`
  - `NeighborRoom->SetConnectedRoom(OppositeDir(Dir), Room)`

- 디버그 로그
  - 각 연결 설정 시 UE_LOG로 양 끝 좌표와 방향 인덱스를 출력해 검증

### 3. 입구와 벽 스폰

- `PlaceWallsAndEntrances(OutRoomMap)` 단계
  - 각 `ACMRoom`에 대해 `GetConnectedRooms()`로 상하좌우 연결 상태 조회
  - 네 방향에 대해
    - 연결된 방이 있으면 Entrance 스폰
    - 없으면 Wall 스폰

- `ACMRoom::SpawnBorderElement`
  - 각 방향별 `USceneComponent`(North/South/East/West EntrancePoint)를 기준으로 좌표와 회전값 계산
  - `RoomEntranceClass` 또는 `RoomWallClass`를 사용해 액터 스폰
  - 이미 한 번 스폰된 Border는 재사용해 중복 스폰 방지

---

## 레벨 스트리밍 구조

### 1. ACMRoom과 StreamingLevelName

- `ACMRoom`에 추가된 프로퍼티
  - `UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Streaming") FName StreamingLevelName;`
- 역할
  - 각 방이 **어떤 서브 레벨과 연결되는지**를 에디터에서 직접 지정 가능
  - 예: `L_StreamingTest1`, `L_StreamingTest2` 같은 이름을 방마다 다르게 설정해 사용

- Getter/Setter
  - `FName GetStreamingLevelName() const`로 외부에서 조회
  - `void SetStreamingLevelName(FName InLevelName)`로 런타임 중 변경 가능

### 2. 동적 스트리밍 인 함수: StreamingLevelStreamIn

- 진입점
  - `void ACMRoom::StreamingLevelStreamIn()`
  - 방이 활성화될 때, 혹은 입구를 통해 진입할 때 호출하는 것을 상정

- 처리 흐름
  - `World`와 `StreamingLevelName` 유효성 검사
  - `StreamingLevelName`을 레벨 애셋 이름으로 보고, 경로 문자열 생성
    - 현재 구현 예
      - `StreamingLevelName = "L_StreamingTest1"`
      - `LevelPath = "/Game/MainStage/L_StreamingTest1"`
  - `Room`의 월드 위치를 가져와 스트리밍 레벨의 기준 위치로 사용
    - `RoomLocation = GetActorLocation()`
  - `ULevelStreamingDynamic::LoadLevelInstance` 호출
    - 매번 새로운 스트리밍 레벨 인스턴스를 **동적으로 생성**
    - 인자
      - `World`
      - `LevelPath` (패키지 경로)
      - `RoomLocation`
      - `FRotator::ZeroRotator`
      - `bSuccess` (성공 여부)

- 결과
  - 호출할 때마다 해당 레벨이 **Room 위치에 복제되듯이 로드**
  - 여러 Room에서 같은 `StreamingLevelName`을 사용하면, 같은 레벨이 여러 위치에 여러 인스턴스로 생성되는 효과

- 성공/실패 로그
  - 실패 시
    - `StreamingLevelStreamIn: Failed to dynamically load level '...' for Room ...`
  - 성공 시
    - `StreamingLevelStreamIn: Dynamically loaded level '...' at Room ... Location=(x, y, z)`

### 3. Room 생성과 스트리밍의 연결

- Room 생성 시점
  - `UCMMapGenerateLogicBaseComponent::GenerateRoom` 안에서 방 액터가 스폰됩니다
- 스트리밍 호출 시점
  - 현재 코드에서는 예시로 `ACMRoom::ExcuteSpawnRoom`에서
    - `StreamingLevelStreamIn();`
    - `SpawnBorderElement(DirectionIndex, bIsEntrance);`
  - 특정 방향으로 출입구를 생성하는 타이밍에 스트리밍을 함께 트리거하는 구조

- 활용 아이디어
  - 플레이어가 특정 방에 입장할 때 해당 방의 서브 레벨을 Stream In
  - 반대로 이전 방에서 멀어졌을 때 Stream Out 함수(추가 구현)를 호출해 메모리 사용량 관리
  - Room 타입(일반/보스/보물)에 따라 서로 다른 서브 레벨을 바인딩해 다양한 룸 구성을 만듦

---

## 구현 결과

![](/assets/images/old/e74e0a32-8ddb-4396-9313-ec1ac8829845-image.png)


---

## 마치며
이번 글에서는 적용한 맵 생성과 레벨 스트리밍 구조를 정리해 보았습니다. 격자 기반 DFS 스패닝 트리 알고리즘을 이용해 항상 연결된 방 그래프를 만들고, 시작점에서의 거리 정보를 활용해 보스 방과 보물 방을 자연스럽게 배치하였습니다. 이후 방의 크기를 기반으로 월드 좌표를 계산해 액터를 스폰하고, 인접 정보에 따라 입구와 벽을 자동으로 구성하는 과정을 정리해 보았습니다.

또한 각 방에 스트리밍 레벨 이름을 직접 바인딩할 수 있는 구조를 만들고, `ULevelStreamingDynamic::LoadLevelInstance`를 통해 방 위치에 맞춰 서브 레벨을 동적으로 로드하는 방식을 도입하였습니다. 이를 통해 동일한 레벨 자산을 여러 방에서 재사용하거나, 방 타입에 따라 서로 다른 레벨 레이아웃을 바인딩하는 등 확장성이 높은 구조를 갖추게 되었습니다. 

