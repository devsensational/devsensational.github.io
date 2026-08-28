---
title: "[Project Arc] 맵 생성 시 Entrance 비정상 생성 문제 해결"
description: "이번 글에서는 Map Generator를 구현하면서, 방(Room) 경계에 배치되는 Entrance(문/통로)들이 비정상적으로 여러 개씩 생성되거나, 잘못된 방향에 배치되는 문제를 어떻게 추적하고 해결했는지 정리해 보겠습니다."
date: 2025-11-24T09:58:46.678Z
tags: ["project arc","ue5","troubleshooting"]
image:
  path: /assets/images/old/50898fc8-43e3-462e-a6b2-22cee65a5c51-image.png
categories: [Project, Project CM + Project Arc]
---
이번 글에서는 Map Generator를 구현하면서, 방(Room) 경계에 배치되는 Entrance(문/통로)들이 비정상적으로 여러 개씩 생성되거나, 잘못된 방향에 배치되는 문제를 어떻게 추적하고 해결했는지 정리해 보겠습니다.

---

## 1. 문제 상황 정리

- 증상 요약
  - 같은 위치(두 방 사이의 경계)에 Entrance(문 같은 Border 액터)가 **겹쳐서 여러 개 생성**됨

- 관련 주요 컴포넌트
  - `UCMMapGenerateLogicBaseComponent::GenerateRoom()`
    - DFS로 격자 기반 방 위치(`FCMRoomPosition`)를 생성
    - `OutRoomMap: TMap<FCMRoomPosition, ACMRoom*>` 에 방 스폰 결과 저장
  - `UCMMapGenerateLogicBaseComponent::PlaceWallsAndEntrances()`
    - `OutRoomMap`을 순회하면서 각 방향에 Wall / Entrance 스폰
  - `ACMRoom::SpawnBorderElement()`
    - 실제 Entrance / Wall 액터를 스폰하고, `RoomBorderActors[4]` 에 캐시

이 세 곳의 로직이 서로 어떻게 엮이는지 이해하는 것이 문제 해결의 핵심이었습니다.

---

## 2. 1차 원인: 방향 인덱스(상/좌/하/우) 불일치

### 2-1. GenerateRoom과 DirectionX/DirectionY의 불일치

- GenerateRoom 내부 정의
  - 방향 인덱스 체계(0~3)를 다음과 같이 사용하고 있었습니다.
    - `DirOffset[4] = {(0,1), (1,0), (0,-1), (-1,0)}`
    - `DirIndexFromDelta(DX, DY)` → 0:Up, 1:Left, 2:Down, 3:Right
    - `OppositeDir(Dir)` → 0↔2, 1↔3

- PlaceWallsAndEntrances에서 사용하던 배열 (초기 상태)
  - `DirectionX[4] = {1, 0, -1, 0};`  // 우, 하, 좌, 상
  - `DirectionY[4] = {0, -1, 0, 1};` // 우, 하, 좌, 상
  - 즉, 0:Right, 1:Down, 2:Left, 3:Up 구조였고, GenerateRoom의 0:Up,1:Left,2:Down,3:Right 와 **정반대 순서**였습니다.

- 이로 인한 문제
  - 방의 좌표(`FCMRoomPosition`)와 그래프(Adjacency, ConnectedRooms)는 **상/좌/하/우** 기준으로 잘 생성됨
  - 하지만 Wall/Entrance 판단은 **우/하/좌/상** 기준으로 검사
  - 결과적으로, 바로 옆에 방이 있어도 "없는 것처럼" 판단하거나, 반대로 다른 방향을 인접한 것으로 취급하는 문제가 발생
  - 눈으로 보면 방 배치는 그럴싸한데, 문과 벽이 이상한 방향에 생성되어 전체가 어그러져 보임

### 2-2. 해결: 모든 방향 관련 정의를 상/좌/하/우로 통일

- 조치
  - `UCMMapGenerateLogicBaseComponent` 헤더에서 `DirectionX/DirectionY` 를 다음과 같이 수정:
    - `DirectionX[4] = { 0, -1,  0,  1};` // 상, 좌, 하, 우
    - `DirectionY[4] = { 1,  0, -1,  0};` // 상, 좌, 하, 우
  - 이렇게 해서 다음 4개가 모두 동일한 인덱스 체계(0:Up,1:Left,2:Down,3:Right)를 사용하도록 맞추었습니다.
    - `DirOffset`
    - `DirIndexFromDelta`
    - `OppositeDir`
    - `DirectionX/DirectionY` 및 `ACMRoom::ConnectedRooms[4]` / `RoomBorderActors[4]`

- 교훈
  - 방향 인덱스/좌표계를 여러 곳에서 정의할 때는 **하나의 기준(예: 상/좌/하/우)** 을 정하고, 전역적으로 사용해야 디버깅이 쉬워집니다.

---

## 3. 2차 원인: SpawnBorderElement의 인덱스 버그로 인해 Entrance 다중 스폰

### 3-1. 증상: 같은 경계에 Entrance가 여러 개 생김

- 특정 두 방 사이에 문이 한 쌍만 있어야 하는데, 실제로는 같은 위치에 Entrance 액터가 여러 개 겹쳐서 생성됨
- 처음에는 "PlaceWallsAndEntrances에서 같은 경계를 두 번 처리(A→B, B→A)해서 그런가?" 정도로 추측

### 3-2. SpawnBorderElement 내부의 중복 방지 로직 분석

- 원래 의도
  - `ACMRoom::SpawnBorderElement(int32 DirectionIndex, bool bIsEntrance)` 는 같은 방향으로 여러 번 호출되더라도 **한 번만 SpawnActor** 하고, 이후에는 캐싱된 액터 포인터를 재사용해야 했습니다.
  - 중복 방지 코드 (초기 상태):
    - `if (RoomBorderActors[DirectionIndex]) return RoomBorderActors[DirectionIndex];`
- 문제 구간
  - 스폰 후 반대편 룸에도 같은 BorderActor를 공유해 주려던 로직:
    - `if (ConnectedRooms[DirectionIndex + 2 % 4])`
    - `ConnectedRooms[DirectionIndex + 2 % 4]->RoomBorderActors[DirectionIndex] = SpawnedActor;`

- 버그 1: 연산자 우선순위 실수
  - `DirectionIndex + 2 % 4` 는 `DirectionIndex + (2 % 4)` 로 계산됨 → `DirectionIndex + 2`
  - 의도는 `(DirectionIndex + 2) % 4` 로 0↔2, 1↔3 매핑이었지만, 실제로는
    - 0 → 2 (우연히 맞음)
    - 1 → 3 (우연히 맞음)
    - 2 → 4 (배열 범위 밖)
    - 3 → 5 (배열 범위 밖)
  - 이로 인해 `ConnectedRooms` 배열 범위를 벗어나 잘못된 메모리를 읽거나 쓰게 되고, `RoomBorderActors` 중복 체크가 붕괴될 위험이 생겼습니다.

- 버그 2: 반대편 룸에 잘못된 인덱스로 저장
  - `ConnectedRooms[DirectionIndex + 2 % 4]->RoomBorderActors[DirectionIndex] = SpawnedActor;`
  - 반대편 룸에서는 **반대 방향 인덱스(OppDir)** 에 저장해야 하는데, 여전히 `DirectionIndex` 를 사용하고 있었습니다.
  - 예를 들어, 현재 방에서 Up(0) 방향 Entrance를 만들 때 반대편(Down 방향)의 인덱스는 2가 되어야 하는데, 잘못된 인덱스에 기록될 수 있습니다.

- 결과
  - 중복 방지용 `RoomBorderActors[DirectionIndex]` 또는 이웃 룸의 `RoomBorderActors` 가 꼬이면서,
  - 같은 경계를 여러 번 처리할 때마다 `SpawnActor` 가 재호출되어 Entrance가 계속 쌓이는 현상으로 이어졌습니다.

### 3-3. 해결: SpawnBorderElement 로직 수정

- 수정 포인트
  - 반대 방향 인덱스를 정확히 계산:
    - `const int32 OppDir = (DirectionIndex + 2) % 4;`
  - 현재 룸과, 연결된 반대편 룸 모두에 동일 BorderActor를 공유:
    - 현재 룸:
      - `RoomBorderActors[DirectionIndex] = SpawnedActor;`
    - 반대편 룸이 이미 연결되어 있다면:
      - `ConnectedRooms[OppDir]->RoomBorderActors[OppDir] = SpawnedActor;`

- 핵심 아이디어
  - **경계 하나(두 방 사이)에 Border 액터는 하나만 존재**해야 하고,
  - 두 방은 각각 자신의 `RoomBorderActors[해당 방향]` 에서 동일한 액터 포인터를 가지도록 설계
  - 이렇게 하면, A→B, B→A 어느 쪽에서 먼저 `SpawnBorderElement` 를 호출해도,
    - 최초 1회만 SpawnActor가 실행되고,
    - 이후에는 캐싱된 포인터를 재사용하게 됩니다.

---

## 4. 3차 원인: 쿼드트리 기반 생성 과정에서의 이슈 (물리적 인접 Room 문제)

### 4-1. 문제 인식

- 맵을 쿼드트리(QuadTree) 기반으로 생성하다 보니, 논리적인 그래프/트리 상에서의 인접 관계와 실제 격자 좌표 상의 물리적 인접 관계가 항상 일치하지 않는 문제가 발생
    - 예시 상황
      - 쿼드트리의 어떤 노드가 서브 트리로 분기되면서, 실제로는 (0,0)과 (1,0) 같은 이웃 타일이 물리적으로는 맞닿아 있지만,
      - 트리 구조 상으로는 서로 다른 브랜치에 속해 있어 "인접 노드"로 간주되지 않는 경우가 발생
- 따라서, Room에서 캐싱한 ConnectedRooms[]으로는 인접한 방이 존재하는지 확인할 수 있는 방법 X
- 방이나 Border가 없다고 판단되어 벽을 생성하는 문제 발생

### 4-2. 해결: FCMRoomPosition 기반 재캐싱

- 해결 전략: FCMRoomPosition 기반 재캐싱
  - 트리/그래프 상의 인접 정보(Adjacency)에만 의존하지 않고, **항상 최종 좌표(FCMRoomPosition)를 기준으로 인접성을 재검증**하도록 설계 방향을 변경
  - 구체적으로는:
    - 쿼드트리 분기, DFS/스패닝 트리 생성 등을 모두 마친 뒤,
    - 최종적으로 `OutRoomMap` 에 담긴 `(FCMRoomPosition → ACMRoom*)` 정보를 다시 순회하면서
    - 각 좌표의 상/좌/하/우 방향에 대해 직접 `OutRoomMap.Find(NeighborPos)` 를 호출
    - 이렇게 해서 물리적으로 인접한 방들만 `ConnectedRooms` 로 다시 묶어 주도록 후처리
  - 이 재캐싱 단계 덕분에
    - 쿼드트리 상으로는 떨어진 브랜치에 있더라도, 실제 그리드 상에서 붙어 있는 방들은 모두 인접 방으로 인식
    - Entrance/Wall 생성 로직은 오직 `FCMRoomPosition` 기반 인접성에만 의존하게 되어, 트리 구조에 의해 왜곡되지 않음


### 4-3: 효과

  - 최종적으로는 **격자 상에서 인접한 방들끼리는 항상 ConnectedRooms가 양방향으로 일관되게 채워짐**
  - 쿼드트리/그래프 구조가 어떻게 변하더라도, FCMRoomPosition 기반 재캐싱 과정 덕분에 Entrance/Wall 스폰 로직이 올바른 인접 정보를 참조할 수 있게됨

---
![](/assets/images/old/50898fc8-43e3-462e-a6b2-22cee65a5c51-image.png)

이번 트러블슈팅을 통해, 단순히 "Entrance가 여러 개 생긴다"는 증상을 해결하는 데에도 여러 층위의 문제가 겹쳐 있을 수 있음을 체감했습니다. 방향 인덱스와 좌표계 정의가 조금만 어긋나도 전체 구조가 틀어지고, 작은 연산자 우선순위 실수 하나가 메모리 오염과 중복 스폰으로 이어질 수 있음을 경험했습니다. 

앞으로는 방향/인덱스/좌표 체계를 프로젝트 초기에 명확히 문서화하고, 경계(Entrance/Wall)와 같은 공유 리소스는 "한 번만 스폰, 양쪽에서 공유"라는 설계를 기본 원칙으로 삼으려 합니다.

