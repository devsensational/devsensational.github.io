---
layout: page
title: "Project Arc(Project CM)"
permalink: /portfolio/portfolio_project_arc/
---

## 프로젝트 개요
---

![image.png](/assets/images/portfolio_project_arc_images/image.png)

- **프로젝트 명:** Project Arc (Project CM에서 피벗 됨)
- **역할**
    - GameMode 및 State 구현
    - 로딩 시퀀스 및 클라이언트 동기화 시스템 구현
    - 절차적 맵 생성 구현
    - Tree형 NPC 대화 및 액션(상호작용) 구현
    - 서버권위 상점 구현
- **개발 환경**
    - Unreal 5.6.1
    - C++
    - PC/Windows
- **기간:** 2025.10.28 ~ 2026.01.12
- **인원:** 8명

## 핵심 기능
---

### 1. 로비 및 클라이언트 동기화 시스템

> **안정적인 멀티플레이 로비 환경을 위해 클라이언트 로딩 시퀀스를 제어하고, 네트워크 비동기성으로 인한 동기화 경합 문제를 해결한 시스템을 설계/구현했습니다.**

#### 기술적 포인트

- **클라이언트 로딩 시퀀스 제어 (로딩 3단계 분리)**
    - 동기화 대상 컴포넌트 준비 완료 후 `OnLoadBegin` → `OnLoadUI` → `OnLoadCompleted` 3단계 순차 로딩 진행
    - 각 단계를 `NextTick`으로 예약 및 브로드캐스트하여 안정적인 초기화 보장
    - 팀원들이 로딩 시퀀스에 기능을 쉽게 추가할 수 있도록 `DECLARE_MULTICAST_DELEGATE`를 통한 바인딩 지원
    - 블루프린트에 노출되지 않는 C++ 전용 델리게이트를 사용함으로써, 무분별한 외부 접근으로 인해 객체지향의 캡슐화가 훼손되고 의존성이 꼬이는 문제를 방지
- **PlayerState Replicated 변수 동기화 경합 해결 (상세 내용은 트러블 슈팅 1번 항목 참조)**
    - `BeginPlay`와 `OnRep` 간 네트워크 초기화 비동기 문제로 인한 로비 접속자 리스트 누락/중복 현상 해결
    - `SetTimerForNextTick`을 활용, `GameState` 초기화 완료 시점까지 처리 지연 및 안전한 목록 추가 보장
    - `bAddedToLobby` 플래그 도입으로 `REPNOTIFY_Always` 재호출 상황에서도 멱등성 확보
- **안정적인 플레이어 세션(입퇴장) 관리**
    - 서버 Authority 환경 및 특수 로그인 흐름에서 누락되는 기존 `AddPlayerState` / `RemovePlayerState` 구조 개선
    - `GameMode`의 `PostLogin` / `Logout` 오버라이드 및 이벤트를 통한 `GameState` 브로드캐스트 적용

#### 핵심 기여

- 클라이언트 로딩 시퀀스 및 멀티플레이 로비 제어 구조 **전체 설계 및 구현**
- 비동기 네트워크 환경에서의 상태 동기화 및 렌더링 경합 문제 해결
- 서버 권한 기반의 안정적인 세션 입장/퇴장 파이프라인 구축

#### 실행 결과

![로딩 시퀀스 순차 실행](/assets/images/old/bd70a123-80c5-44c4-b779-6563b9b1f387-image.png)
_Sync가 모두 완료된 후 차례대로 Load 메소드를 실행하는 것을 볼 수 있습니다_

![로비 플레이어 리스트 출력](/assets/images/old/c35883c4-fd0f-4213-a6ef-5f5cfab54cc9-image.png)
_본인을 제외한 다른 클라이언트들이 로비 리스트에 정상적으로 출력됩니다_

![입퇴장 호출 검증](/assets/images/old/7e09ef98-acf9-4b3b-a753-49c38cb7c318-image.png)
_GameMode PostLogin / Logout을 통해 입장 및 퇴장 이벤트가 확실히 호출됨을 검증했습니다_

#### 구현 과정

[[Project CM] 클라이언트 동기화를 위한 로딩 시퀀스 구현]({% post_url 2025-10-29-[Project CM] 클라이언트 동기화를 위한 로딩 시퀀스 구현 %})

[[Project CM] PlayerState 추가/제거 함수 문제 발견 및 해결 방안]({% post_url 2025-10-30-[Project CM] PlayerState 추가제거 함수 문제 발견 및 해결 방안 %})

[[Project CM] SetTimerForNextTick을 활용한 PlayerState 동기화 시점 문제 해결]({% post_url 2025-10-31-[Project CM] SetTimerForNextTick을 활용한 PlayerState 동기화 시점 문제 해결 %})

---

### 2. 시드 기반 **Procedural Map** 생성

![실제 생성된 지형](/assets/images/portfolio_project_arc_images/image%201.png)

>**시드 기반 Procedural Map + 데이터 기반 맵 생성 구조를 통해, 확장성과 성능을 동시에 확보한 맵 생성 시스템을 설계/구현했습니다.**

#### 기술적 포인트

- DFS + BFS 혼합 구조 설계
    
    **코드 스니펫**
    
    ```cpp
    // 거리 계산(BFS)로 시작점에서의 거리 파악
    TMap<FCMRoomPosition, int32> Distance;
    Distance.Add(Start, 0);
    TQueue<FCMRoomPosition> Q;
    Q.Enqueue(Start);
    while (!Q.IsEmpty())
    {
        FCMRoomPosition Curr;
        Q.Dequeue(Curr);
        const TArray<FCMRoomPosition>* NeighPtr = Adjacency.Find(Curr);
        if (!NeighPtr) continue;
        for (const FCMRoomPosition& N : *NeighPtr)
        {
            if (!Distance.Contains(N))
            {
                Distance.Add(N, Distance[Curr] + 1);
                Q.Enqueue(N);
            }
        }
    }

    // 리프 노드(차수 1, 시작 제외)를 거리 내림차순으로 정렬
    TArray<FCMRoomPosition> Leaves;
    Leaves.Reserve(Adjacency.Num());
    for (const TPair<FCMRoomPosition, TArray<FCMRoomPosition>>& Pair : Adjacency)
    {
        const FCMRoomPosition& Pos = Pair.Key;
        const int32 Degree = Pair.Value.Num();
        if (Degree == 1 && !(Pos.X == Start.X && Pos.Y == Start.Y))
        {
            Leaves.Add(Pos);
        }
    }
    Leaves.Sort([&Distance](const FCMRoomPosition& A, const FCMRoomPosition& B)
    {
        const int32 DA = Distance.Contains(A) ? Distance[A] : MAX_int32;
        const int32 DB = Distance.Contains(B) ? Distance[B] : MAX_int32;
        return DA > DB; // 먼 순서대로
    });

    // 보스/보물 방 배치 결정
    TSet<FCMRoomPosition> BossPositions;
    TSet<FCMRoomPosition> TreasurePositions;

    const int32 BossToPlace = FMath::Clamp(DesiredBoss, 0, Leaves.Num());
    for (int32 i = 0; i < BossToPlace; ++i)
    {
        BossPositions.Add(Leaves[i]);
    }
    ```
    
- Data-driven 설계 (기획 친화적 구조)
    
    ![image.png](/assets/images/portfolio_project_arc_images/image%202.png)
    
- Actor 기반 월드 구성 자동화
- 재현 가능한 Procedural 시스템 구축

#### 핵심 기여

- Procedural Map Generator **전체 구조 설계 및 구현**
- Room Graph → World 배치 파이프라인 구축
- 데이터 기반 콘텐츠 확장 구조 설계

#### 구현 과정

[[Project Arc] 데이터 기반 Procedural Map Generator + 레벨 스트리밍 구현]({% post_url 2025-11-19-[Project Arc] 데이터 기반 Procedural Map Generator + 레벨 스트리밍 구현 %})

---

### 3. NPC Dialogue & Action 시스템 구현

>**Tree 기반 Dialogue 구조와 Action 시스템을 결합하여, 분기형 대화와 게임 로직 실행을 동시에 처리하는 데이터 기반 NPC 상호작용 시스템을 설계/구현했습니다.**

![56.gif](/assets/images/portfolio_project_arc_images/56.gif)

![58.gif](/assets/images/portfolio_project_arc_images/58.gif)

#### 기술적 포인트

- **Tree 기반 Dialogue Graph 구조**
    - Node (대사) + Edge (선택지) 구조
    - 부모-자식 관계 기반 분기 처리
    - DFS/순회 기반 Dialogue 흐름 탐색
    
    → 복잡한 분기형 스토리 구조를 안정적으로 표현
    
- **Dialogue + Action 분리 설계**
    - Dialogue: “무엇을 보여줄 것인가”
    - Action: “무엇을 실행할 것인가”
    - 구조
        - Dialogue Node → Action Trigger 포함
        - 선택 시 특정 게임 로직 실행
        - 예시) 아이템 상점
    
    → 대화 시스템이 단순 UI가 아닌 **게임 로직 트리거 역할 수행**
    
- **Data-driven Dialogue 시스템**
    
    ![image.png](/assets/images/portfolio_project_arc_images/image%203.png)
    
    - DataTable / 구조체 기반 대화 정의
    - 코드 수정 없이 콘텐츠 확장 가능
    
    → 기획자가 직접 Dialogue 제작 가능
    
- **상태 기반 흐름 제어 (Stateful Dialogue)**
    - 현재 노드 상태 기반 진행
    - 선택지에 따라 다음 노드 동적 결정
    
    → FSM(상태 머신)과 유사한 안정적인 흐름 관리
    
- **UI 자동 생성 및 이벤트 바인딩**
    - 선택지 개수에 따라 UI 동적 생성
    - 버튼 ↔ Dialogue Node 자동 연결
    
    → UI 수정 없이 대화 구조 변경 가능
    
- **Action Execution Pipeline**
    - Dialogue → Action → Game System 연결 구조
    - 이벤트 기반 실행 (Delegate / Callback 구조)
    
    → Dialogue → Gameplay 자연스럽게 연결
    
#### 핵심 기여

- Dialogue Tree 구조 **전체 설계 및 구현**
- Dialogue + Action 분리 아키텍처 설계
- Node 기반 Action Trigger 시스템 구현
- 데이터 기반 Dialogue 관리 구조 구축
- UI ↔ 시스템 연결 자동화 구조 설계

#### 구현 과정

[[Project Arc] Tree 구조의 Dialogue 시스템 구현]({% post_url 2025-12-09-[Project Arc] Tree 구조의 Dialogue 시스템 구현 %})

[[Project Arc] NPC Dialogue & Action 시스템 1차 구현 완료]({% post_url 2025-12-12-[Project Arc] NPC Dialogue & Action 시스템 1차 구현 완료 %})

---

### 4. 서버 권한 기반 Shop 시스템 & 데이터 기반 상점 고도화

![35.gif](/assets/images/portfolio_project_arc_images/35.gif)

> **서버 권한 기반 구조와 데이터 중심 설계를 결합하여, 보안성과 확장성을 동시에 확보한 상점 시스템을 구현했습니다.**

#### 기술적 포인트

- **서버 권한 기반 상점 구조 (Authoritative Server Model)**
    - 구매 로직을 **클라이언트가 아닌 서버에서 처리**
    - 클라이언트는 요청(Request), 서버는 검증(Validate) 후 실행
    - **구조:**
        - Client → RPC 요청
        - Server → 재화 검증 / 구매 처리
        - 결과 → Client 동기화
    
    → 치트 및 데이터 변조 방지 (신뢰성 확보)
    
- **RPC 기반 네트워크 처리**
    - `Server RPC`를 통한 구매 요청 처리
    - 상태 변경 후 클라이언트 동기화
    - 핵심 처리:
        - 구매 요청 → 서버 전달
        - 서버에서 재화 체크
        - 성공 시 결과 반환
    
    → 멀티플레이 환경에서도 일관된 상태 유지
    
- **DataTable 기반 상점 데이터 구조**
    
    ![image.png](/assets/images/portfolio_project_arc_images/image%204.png)
    
    - 아이템 정보를 DataTable로 분리
    - 가격 / 설명 / 타입 등 데이터 관리
    
    → 코드 수정 없이 콘텐츠 확장 가능
    
- **UI 캐싱 구조 (성능 최적화)**
    - 상점 UI 생성 시 데이터 캐싱 적용
    - 반복 생성/로드 방지
    
    → UI 생성 비용 감소 및 성능 향상
    
- **수량 증감 시스템 (UX 개선)**
    - +/- 버튼 기반 수량 조절
    - 최소/최대 제한 처리
    - 수량 기반 가격 계산
    
    → 사용자 구매 경험 개선
    
- **UI ↔ 데이터 동기화 구조**
    - UI 상태와 실제 데이터 상태 일관성 유지
    - 변경 시 즉시 반영
    
    → UI 오류 및 상태 불일치 방지

#### 핵심 기여

- 서버 권한 기반 상점 구조 **전체 설계 및 구현**
- RPC 기반 구매 처리 시스템 구축
- DataTable 기반 데이터 관리 구조 설계
- UI 캐싱을 통한 성능 최적화
- 수량 증감 UI 및 로직 구현
- 클라이언트-서버 동기화 구조 설계

#### 구현 과정

[[Project Arc] 서버 권한 상점 컨텐츠 구성 (UI, 캐싱, Data Table, RPC)]({% post_url 2025-12-26-[Project Arc] 서버 권한 상점 컨텐츠 구성 (UI, 캐싱, Data Table, RPC) %})

[[Project Arc] 상점 기능 고도화 (컨텐츠 정보 반영, 개수 증감 버튼 등)]({% post_url 2025-12-30-[Project Arc] 상점 기능 고도화 (컨텐츠 정보 반영, 개수 증감 버튼 등) %})

## 트러블 슈팅
---

### 1. 멀티플레이 환경의 PlayerState 네트워크 동기화 경합 및 중복 문제 해결

#### 문제 상황
- 로비에서 클라이언트 접속 시, 서버에서 클라이언트로 `PlayerState`의 닉네임(`PendingNickname`)을 동기화하는 과정에서 두 가지 치명적인 문제가 발생
- **누락 문제:** 간헐적으로 로비 접속자 리스트에 접속한 플레이어의 닉네임이 정상적으로 등록되지 않음
- **중복 문제:** 동일한 플레이어가 리스트에 여러 번 중복 추가되는 현상 발생

#### 원인 분석
- **네트워크 복제와 월드 초기화의 비동기성 (타이밍 경합):**
    - 언리얼 엔진 네트워크 흐름 상 `PlayerState`의 Replicated 변수들이 클라이언트에 도착하는 시점이 맵의 `BeginPlay()` 시점과 일치한다고 보장할 수 없음
    - 변수가 복제되어 `OnRep` 콜백이 정상적으로 호출되더라도, 그 시점에 로비 리스트를 관리하는 `GameState`가 아직 셋업되지 않았다면 (null 상태) 참조에 실패하여 리스트 추가가 무시되는 타이밍 경합이 발생함
- **복제 알림의 재진입:**
    - 클라이언트 측에서 확실한 동기화를 위해 `REPNOTIFY_Always` 옵션을 사용했으나, 이로 인해 변수 값이 동일하더라도 `OnRep`이 지속적으로 호출되며 리스트 추가 로직이 중복으로 실행될 여지가 있었음

#### 해결 방법
**1. SetTimerForNextTick을 활용한 초기화 경합 해결**
- `OnRep` 호출 시 `GameState`의 존재 여부를 먼저 확인
- `GameState`가 아직 준비되지 않았다면 실패 처리하지 않고, `SetTimerForNextTick`을 활용해 **리스트 갱신 로직 실행을 다음 프레임(Tick)으로 연기시킴으로써 월드 초기화 완료 이후의 안전한 데이터 접근을 보장**

**2. 가드 플래그(bAddedToLobby)를 통한 멱등성 보장**
- `PlayerState` 내부에 `bAddedToLobby` 상태 플래그를 추가
- 로비 리스트에 이미 추가된 상태라면 조기 종료(Return) 처리하여, `REPNOTIFY_Always` 설정으로 인한 `OnRep` 다중 호출이나 지연 처리 상황에서도 단 1회만 등록되도록 방어 로직 구현

**3. 초기값 명시로 확실한 복제 시점 제공**
- 서버의 `BeginPlay()`에서 `PendingNickname`의 초기값을 명확하게 셋업하여 Replication 파이프라인이 안정적으로 시작되도록 유도

#### 결과
- 단일/다중 클라이언트 동시 접속이나 느린 초기화 시뮬레이션 환경에서도 리스트 누락이나 렌더링 꼬임 없이 유저 목록이 1회씩 정상 등록됨을 보장
- 로비 씬과 같이 데이터 복제 직후 다른 서브시스템과 즉시 상호작용해야 하는 환경에서의 네트워크 초기화 안정성을 대폭 향상

---

### 2. 맵 생성 시 Entrance 비정상 생성 문제 해결

#### 문제 상황

- Procedural Map 생성 과정에서 **Entrance / Wall이 잘못 생성되는 문제 발생**
- 특히:
    - 실제로 인접한 Room 사이에 벽이 생성됨
    - 연결되어야 할 구간이 막히는 현상 발생

**→ 논리적으로는 떨어져 있지만, 물리적으로는 붙어 있는 Room을 인식하지 못함**

#### 원인 분석

- 맵 생성 과정에서 **QuadTree + DFS 기반 구조**를 사용하면서 아래 내용이 서로 불일치
    - **논리적 인접 관계 (Tree / Graph)**
    - **물리적 인접 관계 (Grid 좌표)**
    
> 💡 **예시**
> 
> - Room A → (0,0)
> - Room B → (1,0)
> 
> ⇒ 실제로는 **격자 상에서 인접**
> 
> 하지만:
> - 서로 다른 QuadTree 브랜치에 존재
> - Graph 상에서는 연결 정보 없음
> 
> ---
> 
> **결과적으로 발생한 문제**
> - `ConnectedRooms[]` 기반 로직이 실패
> - 인접 방이 존재함에도:
>     - 연결 안 된 것으로 판단
>     - Wall 생성
>     - Entrance 미생성

#### 해결 방법

**1. FCMRoomPosition 기반 재캐싱 도입**

> 💡 **기존:**
> - ConnectedRooms[] (Graph 기반)
> 
> **변경:**
> - **FCMRoomPosition (Grid 좌표 기반)**

**2. 후처리 단계(Post-process) 추가**

- 맵 생성 완료 이후:
    1. QuadTree 생성
    2. DFS / Spanning Tree 생성
    3. Room 생성 완료
    4. **OutRoomMap 기반 재캐싱 수행**
    
    **→ 좌표 기반으로 직접 인접성 판단**

**3. Entrance / Wall 생성 기준 변경**

> 💡 **기존:**
> - Graph 연결 여부 기준
> 
> **변경:**
> - **FCMRoomPosition 기반 인접성만 사용**

→ **트리 구조의 왜곡 영향 제거**

#### 결과

![image.png](/assets/images/portfolio_project_arc_images/image%205.png)

| 항목                 | 개선 결과                           |
| -------------------- | ----------------------------------- |
| 인접성 판단 오류     | **100% 제거**                       |
| Entrance 생성 정확도 | **완전 일치**                       |
| Wall 생성 오류       | 완전 제거                           |
| 맵 구조 일관성       | Graph 구조와 무관하게 **항상 보장** |

#### 해결 과정

[[Project Arc] 맵 생성 시 Entrance 비정상 생성 문제 해결]({% post_url 2025-11-24-[Project Arc] 맵 생성 시 Entrance 비정상 생성 문제 해결 %})

---

### 3. GameStarter NPC 구현 및 Remote Client 필터링 문제 해결

![57.gif](/assets/images/portfolio_project_arc_images/57.gif)

#### 문제 상황

- 멀티플레이 환경에서 **GameStarter NPC가 특정 클라이언트에서 정상적으로 동작하지 않는 문제 발생**
- 일부 클라이언트에서는:
    - NPC가 보이지 않거나
    - 상호작용이 불가능한 상태 발생
- 특히 **Remote Client 환경에서만 문제 발생**

#### 원인 분석

**1. 클라이언트 필터링 로직 문제**

- NPC 생성 및 처리 로직이 **클라이언트 기준으로 필터링되고 있었음**
- 특정 조건에서 Remote Client가:
    - NPC를 생성/인식하지 않음
    - 혹은 동기화 대상에서 제외됨

**2. 서버-클라이언트 책임 분리 문제**

- 일부 NPC 처리 로직이 **클라이언트에 의존**
- 이로 인해:
    - 클라이언트 상태에 따라 결과가 달라짐
    - 네트워크 환경에서 일관성 깨짐

**3. 동기화 범위(Scope) 설계 미흡**

- NPC가 모든 클라이언트에 동일하게 전달되지 않음
- Remote Client는 일부 데이터만 수신

→ NPC 상태 불일치 발생

#### 해결 방법

**1. 서버 중심 구조로 전환**

- NPC 생성 및 상태 관리 책임을 **서버로 완전 이관**
- 클라이언트는 단순 렌더링 및 입력 처리만 담당

구조:

- Server → NPC 생성 및 상태 관리
- Client → 서버 데이터 기반 표시

**2. Remote Client 필터링 로직 수정**

- 클라이언트별 필터링 제거
- 모든 클라이언트가 동일한 NPC 데이터를 수신하도록 구조 변경

**3. 동기화 구조 개선**

- NPC 생성 시:
    - 전체 클라이언트에 브로드캐스트
- 상태 변경 시:
    - 변경 사항만 전송 (Delta Sync)

**4. NPC 초기화 흐름 재설계**

- 접속 시:
    - 기존 NPC 상태를 서버에서 전달
- 이후:
    - 이벤트 기반으로 상태 업데이트

**변경된 상호작용 Sequence Diagram 보기**

![image.png](/assets/images/portfolio_project_arc_images/image%206.png)

#### 결과

| 항목          | 개선 결과                                  |
| ------------- | ------------------------------------------ |
| NPC 표시 문제 | 모든 클라이언트에서 **100% 동일하게 표시** |
| 상호작용 오류 | Remote Client에서도 **정상 동작 보장**     |
| 동기화 안정성 | 클라이언트 간 상태 불일치 제거             |
| 네트워크 구조 | 서버 중심 구조로 안정성 확보               |

#### 해결 과정

[[Project Arc] GameStarter NPC 구현 및 Remote Client 필터링 문제 해결]({% post_url 2026-01-06-[Project Arc] GameStarter NPC 구현 및 Remote Client 필터링 문제 해결 %})

<br><br>

<div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
  <a href="/portfolio/" style="display: inline-block; padding: 14px 28px; font-size: 1.05rem; font-weight: 600; color: #495057; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 8px; text-decoration: none; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease-in-out;">
    <i class="fas fa-arrow-left" style="margin-right: 8px; color: #6c757d;"></i> 포트폴리오 리스트로 돌아가기
  </a>
</div>