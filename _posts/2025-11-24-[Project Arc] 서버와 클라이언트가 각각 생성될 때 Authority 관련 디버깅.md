---
title: "[Project Arc] 서버와 클라이언트가 각각 생성될 때 Authority 관련 디버깅 "
description: "리슨 서버/클라이언트 환경에서 Replicate 해야하는 인스턴스가 클라이언트에서도 생성되는 문제가 발생했습니다."
date: 2025-11-24T14:45:54.657Z
tags: ["Project ARC","UE5","트러블슈팅"]
image:
  path: /assets/images/old/7c9c5f59-b43e-41f4-b0e9-3b61be985170-image.png
categories: [Project CM + Project Arc]
---
리슨 서버/클라이언트 환경에서 **Replicate 해야하는 인스턴스가 클라이언트에서도 생성**되는 문제가 발생했습니다. 특히 `bReplicates` 를 켜지 않았는데도 클라이언트에서 액터가 보이고, `HasAuthority()` 로 분기를 나눴다고 생각했는데도 여전히 중복 생성이 일어나는 상황이라, 네트워크 권한(Authority)와 NetMode 개념을 다시 정리할 필요가 있었습니다.

이번 글에서는 `ACMProcedualMapGenerator` + `UCMMapGenerateLogicBaseComponent` + `ACMRoom` 조합으로 작성된 맵 생성 로직에서 어떤 문제가 있었고, 이를 어떻게 디버깅하고 정리했는지 트러블슈팅 과정을 정리합니다.

---

## 1. 상황 정리

### 1.1. 관련 클래스 구조

- `ACMProcedualMapGenerator`
  - 맵 전체를 생성하는 Actor
  - `GenerateMap(int32 InSeed, UCMRoomDataDefinition* InMapData)` 에서 맵 생성 컴포넌트들을 동적으로 생성/교체
  - `MapGenerateLogicComponent` : `UCMMapGenerateLogicBaseComponent` 기반
  - `SpawnPositionSelectorComponent` : 스폰 위치 선택 담당
  - 결과를 `TMap<FCMRoomPosition, TObjectPtr<ACMRoom>> RoomMap` 에 저장

- `UCMMapGenerateLogicBaseComponent`
  - 실제 방 배치, 연결, 보스/보물 방 결정 등 **맵 생성 알고리즘 구현**
  - 주요 함수
    - `ExecuteMapGenerationLogic` : 전체 생성 파이프라인
    - `GenerateRoom` : 좌표 기반 그래프 생성 및 `ACMRoom` 스폰
    - `PlaceWallsAndEntrances` : 각 방 주변에 Entrance/Wall 스폰

- `ACMRoom`
  - 한 개의 방을 나타내는 Actor
  - `RoomBoundsBox`, 4방향 Entrance 포인트, Entrance/Wall 클래스를 보유
  - `ExcuteSpawnRoom(int32 DirectionIndex, bool bIsEntrance)` 에서 실제로 Entrance/Wall Actor 스폰

### 1.2. 문제가 된 코드 (요약)

```cpp
void UCMMapGenerateLogicBaseComponent::PlaceWallsAndEntrances(TMap<FCMRoomPosition, TObjectPtr<ACMRoom>>& OutRoomMap)
{
    ENetMode NetMode = GetWorld() ? GetWorld()->GetNetMode() : NM_Standalone;
    for (const TPair<FCMRoomPosition, TObjectPtr<ACMRoom>>& Pair : OutRoomMap)
    {
        if (ACMRoom* Room = Pair.Value.Get())
        {
            for (int32 i = 0; i < 4; ++i)
            {
                FCMRoomPosition CurrentPos(Pair.Key.X + DirectionX[i], Pair.Key.Y + DirectionY[i]);
                if (OutRoomMap.Contains(CurrentPos))
                {
                    if (NetMode != NM_Client)
                    {
                        UE_LOG(LogTemp, Log, TEXT("HasAuthority: %d, NetMode: %d"),
                            GetOwner()->HasAuthority(),
                            static_cast<int32>(NetMode));
                        Room->ExcuteSpawnRoom(i, true); // Entrance
                    }
                }
                else
                {
                    Room->ExcuteSpawnRoom(i, false); // Wall
                }
            }
        }
    }
}
```

### 1.3. 증상

![](/assets/images/old/d17f6796-d395-4352-aa0e-5a2acf6b5476-image.png)


- `bReplicates` 를 블루프린트에서 켜지 않았는데도, 클라이언트에서 방/Entrance/Wall 이 모두 보임
- `GetOwner()->HasAuthority()` 로 조건을 걸어도, 여전히 **호스트와 클라이언트 양쪽에서 Entrance/Wall 이 각각 생성**됨
- 로그 상으로는 `HasAuthority: 1` 이 **서버와 클라이언트 양쪽에서 모두 찍히는 듯한** 결과

---

## 2. 개념 정리: HasAuthority, NetMode, 복제 유무

### 2.1. HasAuthority()

- `AActor::HasAuthority()` 는 내부적으로 `Role == ROLE_Authority` 를 의미
- 복제된 Actor 의 경우
  - 서버에 있는 인스턴스: `HasAuthority() == true`
  - 클라에 있는 인스턴스: `HasAuthority() == false`
- 하지만 **비복제 Actor** 의 경우
  - 서버에서 스폰된 인스턴스: `HasAuthority() == true`
  - 클라에서 별도로 스폰된 인스턴스: 여기도 그 월드에서 유일한 Actor 라서 `Role = ROLE_Authority` → `HasAuthority() == true`
- 따라서, **"HasAuthority 가 true면 서버"라고 단정하면 안 됨**

### 2.2. NetMode

- `UWorld::GetNetMode()` 로 현재 월드의 네트워크 모드를 알 수 있음
  - `NM_Standalone` (0) : 싱글 플레이
  - `NM_DedicatedServer` (1) : 디디케이티드 서버
  - `NM_ListenServer` (2) : 리슨 서버(호스트)
  - `NM_Client` (3) : 클라이언트
- **"이 코드가 서버에서 실행 중인가?"** 를 알고 싶다면:
  - `World->GetNetMode() == NM_Client` 이면 클라이언트 → 서버 전용 로직은 실행하지 않도록 Early Return
  - 또는 `World->GetNetMode() != NM_Client` 을 서버/호스트 쪽으로 간주해도 됨

---

## 3. 실제 원인 분석

### 3.1. MapGenerator 가 서버/클라에 각각 존재

- `ACMProcedualMapGenerator` 는 단순 `AActor` 이고, `bReplicates` 세팅이나 서버 전용 제약 없이 월드에 배치/생성되어 있었음
- 리슨 서버 + 클라이언트 환경에서
  - 서버 월드에 `ACMProcedualMapGenerator` 한 개
  - 클라이언트 월드에도 `ACMProcedualMapGenerator` 한 개
  - 둘 다 자기 월드에서 유일한 존재 → 둘 다 `HasAuthority() == true`
- `GenerateMap()` 호출 또한 서버/클라 각각에서 트리거되는 구조였기 때문에,
  - `UCMMapGenerateLogicBaseComponent::ExecuteMapGenerationLogic`
  - `UCMMapGenerateLogicBaseComponent::PlaceWallsAndEntrances`
  - `ACMRoom::ExcuteSpawnRoom`
  이 세트가 서버와 클라이언트에서 **각각 한 번씩** 실행됨

### 3.2. PlaceWallsAndEntrances 의 조건

- 초기 버전에서는 `GetOwner()->HasAuthority()` 만 보고 Entrance 를 생성
- 이후 `ENetMode NetMode = GetWorld()->GetNetMode()` 를 도입해 `NetMode != NM_Client` 인 경우에만 Entrance 를 생성하도록 변경
- 하지만 여전히 문제가 남았던 부분:
  - `else` 분기 (`OutRoomMap` 에 인접 방이 없을 때)에서 Wall 스폰은 **권한/NetMode 체크 없이 항상 실행**
  - `ExcuteSpawnRoom` 내부에서도 별도의 `HasAuthority()` 체크가 없으면, 양쪽에서 모두 스폰
- 최종적으로는:
  - 서버 MapGenerator → Entrance + Wall 스폰
  - 클라 MapGenerator → (NetMode 체크 추가 후) Entrance 는 안 만들더라도, Wall 은 만들 수 있음
  - 그리고 `ACMRoom` 이 비복제라면, 서버/클라 각각의 `ACMRoom` 인스턴스도 자기 기준에서는 `HasAuthority() == true`

### 3.3. 로그가 둘 다 1로 찍히는 이유

- `UE_LOG(LogTemp, Log, TEXT("HasAuthority: %d, NetMode: %d"), GetOwner()->HasAuthority(), (int32)NetMode);`
- 위 로그에서:
  - 서버 월드: `HasAuthority = 1`, `NetMode = 2 (ListenServer)` 또는 1 (DedicatedServer)
  - 클라 월드: `HasAuthority = 1`, `NetMode = 3 (Client)` 인 케이스가 가능
- 즉, 단순히 `HasAuthority` 칼럼만 보면 둘 다 1로 찍히기 때문에,
  - **"Authority 를 둘 다 갖고 있는 것 같다"** 는 인상을 받게 됨
  - 실제로는 서로 다른 월드에서 각각 Authority 인 비복제 Actor 일 뿐, 네트워크 복제와는 무관

---

## 4. 해결 전략

### 4.1. 서버/클라이언트 분기 기준을 명확히

- **"맵을 생성하는 로직은 서버/호스트에서만 실행한다"** 를 명확한 정책으로 잡음
- 이를 위해 다음 기준을 사용
  - `UWorld::GetNetMode()` 가 `NM_Client` 이면 → 맵 생성 로직/스폰 로직은 아예 실행하지 않음
  - `HasAuthority()` 는 보조적으로 사용하되, 비복제 Actor 도 Authority 일 수 있다는 점을 항상 염두에 둠


---

## 5. 최종 정리

아래는 Entrance 인스턴스가 정상적으로 Replication On/Off 되는 결과물입니다.

![](/assets/images/old/d2ea2e4f-730b-421d-871c-affa417b1798-image.png)

![](/assets/images/old/78f272d1-e817-4f31-98c3-401dfd5494ca-image.png)


- 언리얼 네트워크에서 `HasAuthority()` 와 `NetMode` 는 비슷해 보이지만, 서로 다른 레이어의 개념이라는 점을 다시 상기
  - `HasAuthority()` : 이 Actor 인스턴스가 **자기 월드에서 서버 역할인지**
  - `NetMode` : 이 월드가 **DedicatedServer / ListenServer / Client / Standalone** 인지
- **비복제 Actor** 는 서버와 클라이언트에서 각각 스폰되면, 둘 다 `HasAuthority() == true` 라는 점이 핵심 포인트
- 따라서, 서버/클라이언트를 분기하고 싶을 때는 다음 우선순위를 지키는 것이 좋다고 정리

- 우선순위
  1. `UWorld::GetNetMode()` 로 **프로세스 레벨(서버/클라) 구분**
     - `NM_Client` 인 경우 서버 전용 로직을 실행하지 않음
  2. `AActor::HasAuthority()` 는 **복제된 Actor 의 서버/클라 인스턴스 구분**에 사용
  3. 스폰 로직이 있는 함수(예: `ExcuteSpawnRoom`) 내부에도 `HasAuthority()` 체크를 두어 이중 방어

- 이번 트러블슈팅을 통해 얻은 교훈

  - 단순히 "Authority 가 true 니까 서버겠지" 라고 생각하면 쉽게 헷갈린다.
  - 맵 생성처럼 월드 전체에 영향을 주는 로직은 **반드시 서버/호스트 한 곳에서만 실행되도록 구조를 잡는 것**이 중요하다.
  - 디버깅 시에는 `HasAuthority` 뿐 아니라 `NetMode` 값도 함께 로그로 남겨야, "어느 월드에서 무슨 역할로" 실행 중인지 명확히 볼 수 있다.