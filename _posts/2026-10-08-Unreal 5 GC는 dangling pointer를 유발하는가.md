---
title: Unreal 5 GC는 dangling pointer를 유발하는가?
date: 2026-10-08 17:40 +0900
category: [UE5]
tags: ["ue5", "cpp"]
description: Unreal GC가 C#처럼 객체 이동을 유발하는지, 그 과정에서 포인터 유효성을 훼손할 수 있는지 직접 실험
math: true
---

## 용어 정리

| 용어                            | 뜻                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------- |
| GC (Garbage Collection)         | 더 이상 쓰이지 않는 메모리를 런타임이 자동으로 회수하는 기법                          |
| Mark & Sweep                    | 루트에서 도달 가능한 객체를 표시하고, 표시되지 않은 객체를 해제하는 GC 방식           |
| Compaction (압축)               | 살아남은 객체를 모아 빈 공간을 없애는 작업. 객체 주소가 바뀜                          |
| Root Set                        | GC 탐색의 시작점이 되는 객체 집합                                                     |
| Full Purge                      | GC가 도달 불가 객체를 표시한 뒤 같은 프레임 안에서 메모리 해제까지 끝내는 모드        |
| Dangling Pointer                | 해제된 메모리를 가리키는 포인터                                                       |
| UB (Undefined Behavior)         | C++ 표준이 결과를 정의하지 않는 동작                                                  |
| Reallocation (재할당)           | 동적 배열이 용량을 넘으면 새 버퍼를 할당하고, 요소를 옮긴 뒤, 옛 버퍼를 해제하는 과정 |
| Slack                           | `TArray`에서 할당은 됐지만 아직 쓰이지 않는 칸 (`Max() - Num()`)                      |
| Trivially Relocatable           | 원시 바이트 복사만으로 다른 주소로 옮겨도 안전한 타입의 성질                          |
| `UPROPERTY`                     | 멤버를 리플렉션 시스템에 등록하는 매크로. GC가 이 참조를 추적함                       |
| `TObjectPtr` / `TWeakObjectPtr` | UE5의 UObject 강한 참조 래퍼 / GC를 막지 않는 약한 참조                               |
| `GUObjectArray`                 | 모든 UObject를 인덱스 슬롯으로 관리하는 엔진 전역 배열                                |
| `GetUniqueID()`                 | UObject가 `GUObjectArray`에서 차지하는 인덱스                                         |
| `UPTRINT`                       | 포인터를 정수로 담는 UE 타입. 해제된 주소를 역참조하지 않고 비교만 하기 위해 사용     |
| PIE / Output Log                | 에디터 안에서 게임을 실행하는 모드 / 에디터 로그 창                                   |
| 에디터 월드 / PIE 월드          | 편집 중인 레벨 / PIE 시작 시 에디터 월드를 복제해 만든 실행용 월드                    |
| GC 감시자 (Sentinel)            | GC가 실제로 돌았는지 알려주는 표지. 참조 없는 객체 10,000개의 약한 포인터 생존 수     |
| 대조군 (Control)                | 의심되는 원인 하나만 빼고 같은 조건으로 돌리는 실험                                   |
| 판별력                          | 가설이 틀렸다면 결과가 달라졌을지의 정도                                              |
| 실행 A / 실행 B                 | 강제 GC를 켠 본 실험 / 강제 GC를 끈 대조군 실험                                       |

## 요약

1. C#(.NET)의 GC는 **압축** 과정에서 객체 주소를 바꿈
2. UE5 GC는 쓰레기 9,000개를 수거하는 동안 **생존 객체 1,000개 중 하나도 옮기지 않음**
3. `TArray`는 **자기 버퍼를 재할당**하므로 요소 주소가 바뀜. 재할당 중 생성자 호출이 **0회**(바이트 복사)이므로 자기 참조 요소는 내부까지 깨짐
4. 파괴된 액터의 `UPROPERTY` 참조는 `Destroy()` 직후가 아니라 **GC 실행 시점**에 null로 바뀜. raw 포인터는 끝까지 null이 아님

## 1. C# GC는 객체를 옮김

- .NET 문서는 GC를 표시 단계, 압축될 객체의 참조를 갱신하는 재배치 단계, 생존 객체를 세그먼트의 오래된 쪽 끝으로 옮기는 압축 단계로 나누어 설명함[^1]
- C#은 GC가 변수를 옮기지 못하게 고정하는 `fixed` 문을 제공함. 고정된 변수의 주소는 해당 문이 실행되는 동안 고정 상태임[^2]
- 언어가 별도의 "고정" 문법을 제공한다는 것은 GC가 객체를 옮긴다는 뜻임

## 2. UE5 GC는 도달이 불가능한 객체를 제거함

### 문서 근거

- Epic Knowledge Base는 UE GC를 표준 Mark & Sweep 수집기로 소개함[^3]
- 엔진은 루트 셋에서 참조 트리를 탐색하고, 탐색되지 않은 UObject를 불필요한 객체로 간주해 제거함[^4]
- 액터나 컴포넌트가 파괴되면, 리플렉션 시스템이 볼 수 있는 참조(`UPROPERTY` 포인터, `TArray` 같은 UE 컨테이너 안의 포인터)를 자동으로 null 처리함. raw 포인터는 엔진이 알지 못하므로 null 처리 대상이 아님[^4]
- `GUObjectArray`의 각 항목(`FUObjectItem`)은 할당된 객체를 가리키는 포인터를 보유함[^5]
- `FWeakObjectPtr`는 대상이 GC되면 `nullptr` 반환이 가능함[^6]
- 문서의 GC 설명에는 "생존 객체를 옮기는" 단계가 등장하지 않음. 그림 1 오른쪽(UE)의 "주소 유지"는 4장의 실험으로 확인함

![압축 GC와 UE 5.6 UObject GC 비교](/assets/images/2026-10-08-ue5_gc/01.png)
_그림 1. 압축 GC와 UE 5.6 UObject GC 비교 (주소 값은 예시)_

## 3. 실험 환경과 방법

### 3.1 실험 설계 포인트

| 구분    | 설계                                                     | 막으려는 함정                                          |
| ------- | -------------------------------------------------------- | ------------------------------------------------------ |
| 실험 1  | GC가 모르는 raw 포인터 사본을 함께 비교 (`raw==tracked`) | GC가 객체를 옮기고 추적 참조만 몰래 고치는 경우를 놓침 |
| 실험 1  | 인덱스 비교는 `same object(index)`로 명명                | 인덱스 유지를 비이동의 증거로 오해                     |
| 실험 1b | 쓰레기 9개마다 생존 객체 1개를 끼워 넣음                 | 생존 객체가 먼저 할당돼 압축 GC여도 안 움직였을 가능성 |
| 실험 3b | 재할당마다 옮겨진 요소 수를 기록                         | 깨진 요소 수의 의미를 추측으로만 설명                  |
| 실험 3c | 재할당 중 복사/이동 생성자 호출 횟수 측정                | "TArray는 생성자를 부르지 않음"을 간접 증거로만 주장   |
| 실험 4  | `pointer value kept`와 `object unchanged`를 분리         | GC와 무관한 동어반복 지표를 GC 증거로 오해             |
| 실험 5  | 강제 GC를 끈 실행 B(대조군) 추가                         | null 처리의 원인을 GC로 단정                           |
| 공통    | 모든 GC 판정 전에 `[GC] sentinel` 확인                   | GC가 돌지 않았는데 "주소가 그대로"라고 결론            |
| 공통    | 해제됐을 수 있는 포인터는 정수 비교만 수행               | 실험 코드 자체가 UB를 일으킴                           |

### 3.2 실행 흐름

- 레벨에 실험용 액터 `AGcExperimentActor` 1개를 배치하고 PIE로 실행함
- GC와 무관한 실험 2, 3, 3b, 3c는 `BeginPlay`에서 즉시 수행함
- GC 실험 1, 1b, 4, 5는 준비 → (강제 GC) → 대기 → 검증 순서로 수행함
- 실행 A와 B는 강제 GC 요청 여부만 다른 구성임

![GC 실험 실행 흐름](/assets/images/2026-10-08-ue5_gc/18.png)
_그림 2. 실험 실행 흐름_

| 실행   | 설정                                                                            | 목적                                    |
| ------ | ------------------------------------------------------------------------------- | --------------------------------------- |
| 실행 A | `bForceGC = true`: `GEngine->ForceGarbageCollection(true)`로 Full Purge GC 요청 | 본 실험                                 |
| 실행 B | `bForceGC = false`: 강제 GC 없음                                                | 대조군 (null 처리의 원인이 GC인지 분리) |

### 3.3 실행 방법

- **1단계**: UE 5.6 C++ 프로젝트에 3.5절의 소스 파일 3개를 추가하고, `YOURPROJECT_API`를 모듈 API 매크로로 교체함
- **2단계**: Development Editor 구성으로 빌드함. `UPROPERTY` 추가가 포함되므로 Live Coding 대신 에디터를 닫고 IDE에서 빌드하는 것을 권장함
- **3단계**: 빈 레벨에 `GcExperimentActor`를 1개만 배치함
- **4단계**: `bForceGC`는 레벨에 배치한 액터의 Details 패널(Experiment 카테고리)에서 토글함

![Details 패널의 bForceGC 토글](/assets/images/2026-10-08-ue5_gc/99.png)
_그림 3. Details 패널의 `bForceGC` 토글_

- **5단계**: Window → Output Log를 열고 검색창에 `[`를 입력함. `[EXP`로 필터링하면 `[RUN]`, `[GC]` 줄이 빠지므로 주의가 필요함
- **6단계 (실행 A)**: PIE 종료 상태에서 `bForceGC = true`, `VerifyDelaySeconds = 2.0`으로 설정함. PIE 실행 후 3초 이상 대기하고 로그를 캡쳐함
- **7단계 (실행 B)**: PIE 종료 상태에서 `bForceGC = false`로 바꾸고 PIE를 실행함. `[GC] sentinel`이 `gc ran=true`이면 자동 GC가 대기 중에 돈 것이므로 `VerifyDelaySeconds`를 `0.5`로 줄여 재실행함
- **8단계**: 같은 로그는 `프로젝트/Saved/Logs/프로젝트명.log`에도 남음

> 안전 수칙: 모든 비교는 `UPTRINT` 정수로만 수행함. 해제됐을 수 있는 포인터(`VictimRaw`, 옛 버퍼 주소)는 역참조하지 않음

#### 설정값은 PIE 종료 상태에서 변경함

- PIE는 시작 시점에 에디터 월드의 액터를 복제해서 실행함
- PIE 실행 중 Details 패널에서 값을 바꾸면 `BeginPlay`가 이미 끝난 복제본만 바뀌므로 실험에 반영되지 않음

![에디터 월드와 PIE 월드의 값 복제](/assets/images/2026-10-08-ue5_gc/02.png)
_그림 4. 값은 PIE 시작 시 에디터 월드에서 복제됨_

### 3.4 실행 모드 확인

| 실행 | `[RUN]` 로그                                         | `[GC] sentinel` 로그                       |
| ---- | ---------------------------------------------------- | ------------------------------------------ |
| A    | `mode=A (forced GC) / verify after 2.0s`             | `garbage alive=0/10000 / gc ran=true`      |
| B    | `mode=B (no forced GC, control) / verify after 2.0s` | `garbage alive=10000/10000 / gc ran=false` |

- 실행 A는 감시자 0/10000으로 GC 실행을 확인함
- 실행 B는 감시자 10000/10000으로 GC 미실행을 확인함. 대조군 조건이 성립함

<!-- TODO: 03.png — 실행 A, Output Log 필터 "[" : [RUN], [GC] sentinel 줄 캡쳐 -->
![실행 A의 실행 모드와 GC 감시자 로그](/assets/images/2026-10-08-ue5_gc/03.png)
_그림 5. 실행 A — `[RUN]`, `[GC] sentinel`_

<!-- TODO: 04.png — 실행 B, Output Log 필터 "[" : [RUN], [GC] sentinel 줄 캡쳐 -->
![실행 B의 실행 모드와 GC 감시자 로그](/assets/images/2026-10-08-ue5_gc/04.png)
_그림 6. 실행 B — `[RUN]`, `[GC] sentinel`_

### 3.5 소스 코드

- 파일 이름을 누르면 전체 코드가 펼쳐짐


<details markdown="1">
<summary><code>GcProbeData.h</code></summary>

```cpp
#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "GcProbeData.generated.h"

UCLASS()
class YOURPROJECT_API UGcProbeData : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY()
    int32 Payload = 0;
};
```

</details>

<details markdown="1">
<summary><code>GcExperimentActor.h</code></summary>

```cpp
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GcExperimentActor.generated.h"

class UGcProbeData;

UCLASS()
class YOURPROJECT_API AGcExperimentActor : public AActor
{
    GENERATED_BODY()

public:
    // 실행 A: true (본 실험) / 실행 B: false (실험 5 대조군)
    UPROPERTY(EditAnywhere, Category = "Experiment")
    bool bForceGC = true;

    // 준비 후 검증까지 대기 시간(초)
    UPROPERTY(EditAnywhere, Category = "Experiment", meta = (ClampMin = "0.1"))
    float VerifyDelaySeconds = 2.0f;

protected:
    virtual void BeginPlay() override;

private:
    // GC와 무관한 동기 실험
    void Exp2_TArrayRealloc();
    void Exp3_SelfPointer();
    void Exp3b_ReallocTrace();
    void Exp3c_CtorCount();

    // GC 실험: 준비
    void Exp1_Prepare();
    void Exp1b_Prepare();
    void Exp4_Prepare();
    void Exp5_Prepare();

    // GC 실험: 검증
    void VerifyAfterGC();
    void Exp1_Verify();
    void Exp1b_Verify();
    void Exp4_Verify();
    void Exp5_Verify();

    // 실험 1 (GarbageWeaks는 GC 감시자로도 사용)
    UPROPERTY() TObjectPtr<UGcProbeData> Kept;
    UGcProbeData* KeptRaw = nullptr;                    // GC가 모르는 사본
    UPTRINT KeptAddrBefore = 0;
    int32 KeptIndexBefore = INDEX_NONE;
    TArray<TWeakObjectPtr<UGcProbeData>> GarbageWeaks;

    // 실험 1b
    UPROPERTY() TArray<TObjectPtr<UGcProbeData>> Survivors;
    TArray<UPTRINT> SurvivorAddrBefore;
    TArray<TWeakObjectPtr<UGcProbeData>> InterleavedGarbage;

    // 실험 4
    UPROPERTY() TArray<TObjectPtr<UGcProbeData>> Slots;
    UPTRINT SlotAddrBefore = 0;
    UPTRINT ObjAddrBefore = 0;

    // 실험 5
    UPROPERTY() TObjectPtr<AActor> VictimTracked;
    UPROPERTY() TArray<TObjectPtr<AActor>> VictimArray;
    AActor* VictimRaw = nullptr;                        // 비교만, 역참조 금지

    FTimerHandle VerifyTimer;
};
```

</details>

<details markdown="1">
<summary><code>GcExperimentActor.cpp</code></summary>

```cpp
#include "GcExperimentActor.h"
#include "GcProbeData.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include <vector>

namespace
{
    constexpr int32 GarbageCount    = 10000;   // 실험 1 쓰레기 (감시자)
    constexpr int32 InterleaveCount = 10000;   // 실험 1b: 10개 중 1개 생존
    constexpr int32 GrowCount       = 1000;    // 실험 2, 3, 3b, 3c, 4 추가 개수

    // 실험 3, 3b: 생성될 때 자기 주소를 기록
    // 생성자를 거쳐 옮겨지면 Self == this, 바이트 복사로 옮겨지면 Self != this
    struct FSelfRef
    {
        const FSelfRef* Self;
        FSelfRef() : Self(this) {}
        FSelfRef(const FSelfRef&) : Self(this) {}
        FSelfRef(FSelfRef&&) noexcept : Self(this) {}
        FSelfRef& operator=(const FSelfRef&) { return *this; }
        FSelfRef& operator=(FSelfRef&&) noexcept { return *this; }
        bool IsIntact() const { return Self == this; }
    };

    // 실험 3c: 복사/이동 생성자 호출 횟수 기록
    struct FCountingElem
    {
        inline static int32 CopyCount = 0;
        inline static int32 MoveCount = 0;
        static void Reset() { CopyCount = 0; MoveCount = 0; }

        int32 Value = 0;
        FCountingElem() = default;
        FCountingElem(const FCountingElem& Other) : Value(Other.Value) { ++CopyCount; }
        FCountingElem(FCountingElem&& Other) noexcept : Value(Other.Value) { ++MoveCount; }
        FCountingElem& operator=(const FCountingElem&) = default;
        FCountingElem& operator=(FCountingElem&&) noexcept = default;
    };

    template <typename ContainerT>
    int32 CountBroken(const ContainerT& Container)
    {
        int32 Broken = 0;
        for (const FSelfRef& Elem : Container)
        {
            if (!Elem.IsIntact()) { ++Broken; }
        }
        return Broken;
    }

    int32 CountAlive(const TArray<TWeakObjectPtr<UGcProbeData>>& Weaks)
    {
        int32 Alive = 0;
        for (const TWeakObjectPtr<UGcProbeData>& Weak : Weaks)
        {
            if (Weak.IsValid()) { ++Alive; }
        }
        return Alive;
    }

    const TCHAR* BoolStr(bool bValue) { return bValue ? TEXT("true") : TEXT("false"); }

    UPTRINT ToAddr(const void* Ptr) { return reinterpret_cast<UPTRINT>(Ptr); }
}

// ───────────────────────── 진입점 ─────────────────────────

void AGcExperimentActor::BeginPlay()
{
    Super::BeginPlay();

    UE_LOG(LogTemp, Display, TEXT("[RUN] mode=%s | verify after %.1fs"),
        bForceGC ? TEXT("A (forced GC)") : TEXT("B (no forced GC, control)"), VerifyDelaySeconds);

    // GC와 무관한 동기 실험
    Exp2_TArrayRealloc();
    Exp3_SelfPointer();
    Exp3b_ReallocTrace();
    Exp3c_CtorCount();

    // GC 실험 준비
    Exp1_Prepare();
    Exp1b_Prepare();
    Exp4_Prepare();
    Exp5_Prepare();

    if (bForceGC)
    {
        GEngine->ForceGarbageCollection(/*bFullPurge*/ true);   // 다음 틱에 Full Purge GC 요청
    }
    GetWorldTimerManager().SetTimer(VerifyTimer, this, &AGcExperimentActor::VerifyAfterGC, VerifyDelaySeconds, false);
}

void AGcExperimentActor::VerifyAfterGC()
{
    const int32 Alive = CountAlive(GarbageWeaks);
    UE_LOG(LogTemp, Display, TEXT("[GC] sentinel | garbage alive=%d/%d | gc ran=%s"),
        Alive, GarbageWeaks.Num(), BoolStr(Alive == 0));

    Exp1_Verify();
    Exp1b_Verify();
    Exp4_Verify();
    Exp5_Verify();
}

// ───────────────────────── 실험 1: GC 전후 UObject 주소 ─────────────────────────

void AGcExperimentActor::Exp1_Prepare()
{
    Kept = NewObject<UGcProbeData>(this);
    KeptRaw = Kept.Get();
    KeptAddrBefore = ToAddr(KeptRaw);
    KeptIndexBefore = static_cast<int32>(KeptRaw->GetUniqueID());

    GarbageWeaks.Reserve(GarbageCount);
    for (int32 i = 0; i < GarbageCount; ++i)
    {
        GarbageWeaks.Add(NewObject<UGcProbeData>(GetTransientPackage()));   // 아무도 참조하지 않음
    }

    UE_LOG(LogTemp, Display, TEXT("[EXP1] prepare | Kept=%p Index=%d | garbage alive=%d/%d"),
        KeptRaw, KeptIndexBefore, CountAlive(GarbageWeaks), GarbageWeaks.Num());
}

void AGcExperimentActor::Exp1_Verify()
{
    UGcProbeData* Now = Kept.Get();
    const int32 IndexNow = static_cast<int32>(Now->GetUniqueID());

    UE_LOG(LogTemp, Display, TEXT("[EXP1] verify  | Kept=%p Index=%d"), Now, IndexNow);
    UE_LOG(LogTemp, Display, TEXT("[EXP1] result  | address unchanged=%s | raw==tracked=%s | same object(index)=%s"),
        BoolStr(ToAddr(Now) == KeptAddrBefore),
        BoolStr(KeptRaw == Now),
        BoolStr(IndexNow == KeptIndexBefore));
}

// ───────────────────────── 실험 1b: 쓰레기 사이에 끼운 생존 객체 ─────────────────────────

void AGcExperimentActor::Exp1b_Prepare()
{
    Survivors.Reserve(InterleaveCount / 10);
    SurvivorAddrBefore.Reserve(InterleaveCount / 10);
    InterleavedGarbage.Reserve(InterleaveCount);

    for (int32 i = 0; i < InterleaveCount; ++i)
    {
        UGcProbeData* Obj = NewObject<UGcProbeData>(GetTransientPackage());
        if (i % 10 == 9)            // 쓰레기 9개 다음에 생존 객체 1개
        {
            Survivors.Add(Obj);
            SurvivorAddrBefore.Add(ToAddr(Obj));
        }
        else
        {
            InterleavedGarbage.Add(Obj);
        }
    }

    UE_LOG(LogTemp, Display, TEXT("[EXP1b] prepare | survivors=%d | garbage alive=%d/%d"),
        Survivors.Num(), CountAlive(InterleavedGarbage), InterleavedGarbage.Num());
}

void AGcExperimentActor::Exp1b_Verify()
{
    int32 Moved = 0;
    for (int32 i = 0; i < Survivors.Num(); ++i)
    {
        if (ToAddr(Survivors[i].Get()) != SurvivorAddrBefore[i]) { ++Moved; }
    }

    UE_LOG(LogTemp, Display, TEXT("[EXP1b] verify  | survivors moved=%d/%d | garbage alive=%d/%d"),
        Moved, Survivors.Num(), CountAlive(InterleavedGarbage), InterleavedGarbage.Num());
}

// ───────────────────────── 실험 2: TArray 버퍼 이동 ─────────────────────────

void AGcExperimentActor::Exp2_TArrayRealloc()
{
    TArray<int32> Arr;
    Arr.Add(0);
    const UPTRINT DataBefore = ToAddr(Arr.GetData());
    UE_LOG(LogTemp, Display, TEXT("[EXP2] grow    | before Num=%d Max=%d"), Arr.Num(), Arr.Max());

    for (int32 i = 1; i <= GrowCount; ++i) { Arr.Add(i); }
    UE_LOG(LogTemp, Display, TEXT("[EXP2] grow    | after  Num=%d Max=%d | buffer moved=%s"),
        Arr.Num(), Arr.Max(), BoolStr(DataBefore != ToAddr(Arr.GetData())));

    TArray<int32> Reserved;
    Reserved.Reserve(GrowCount + 1);
    Reserved.Add(0);
    const UPTRINT ReservedBefore = ToAddr(Reserved.GetData());

    for (int32 i = 1; i <= GrowCount; ++i) { Reserved.Add(i); }
    UE_LOG(LogTemp, Display, TEXT("[EXP2] reserve | Num=%d Max=%d | buffer moved=%s"),
        Reserved.Num(), Reserved.Max(), BoolStr(ReservedBefore != ToAddr(Reserved.GetData())));
}

// ───────────────────────── 실험 3: 재할당 시 요소가 생성자를 거치는가 ─────────────────────────

void AGcExperimentActor::Exp3_SelfPointer()
{
    std::vector<FSelfRef> Vec;
    TArray<FSelfRef> Arr;
    for (int32 i = 0; i < GrowCount; ++i)
    {
        Vec.emplace_back();
        Arr.Emplace();
    }

    UE_LOG(LogTemp, Display, TEXT("[EXP3] self-pointer broken | std::vector=%d/%d | TArray=%d/%d"),
        CountBroken(Vec), static_cast<int32>(Vec.size()), CountBroken(Arr), Arr.Num());
}

// ───────────────────────── 실험 3b: 재할당 시점과 깨진 요소 수 대응 ─────────────────────────

void AGcExperimentActor::Exp3b_ReallocTrace()
{
    TArray<FSelfRef> Arr;
    UPTRINT LastData = 0;
    int32 LastMovedCount = 0;

    for (int32 i = 0; i < GrowCount; ++i)
    {
        const int32 ExistingBefore = Arr.Num();
        Arr.Emplace();

        const UPTRINT Data = ToAddr(Arr.GetData());
        if (Data != LastData)
        {
            UE_LOG(LogTemp, Display, TEXT("[EXP3b] realloc | Num %d -> %d | Max=%d | moved=%d"),
                ExistingBefore, Arr.Num(), Arr.Max(), ExistingBefore);
            LastData = Data;
            LastMovedCount = ExistingBefore;
        }
    }

    const int32 Broken = CountBroken(Arr);
    UE_LOG(LogTemp, Display, TEXT("[EXP3b] result  | last moved=%d | broken=%d | match=%s"),
        LastMovedCount, Broken, BoolStr(LastMovedCount == Broken));
}

// ───────────────────────── 실험 3c: 재할당 중 생성자 호출 횟수 ─────────────────────────

void AGcExperimentActor::Exp3c_CtorCount()
{
    FCountingElem::Reset();
    {
        std::vector<FCountingElem> Vec;
        for (int32 i = 0; i < GrowCount; ++i) { Vec.emplace_back(); }
    }
    const int32 VecCopy = FCountingElem::CopyCount;
    const int32 VecMove = FCountingElem::MoveCount;

    FCountingElem::Reset();
    {
        TArray<FCountingElem> Arr;
        for (int32 i = 0; i < GrowCount; ++i) { Arr.Emplace(); }
    }

    UE_LOG(LogTemp, Display, TEXT("[EXP3c] ctor calls | std::vector copy=%d move=%d | TArray copy=%d move=%d"),
        VecCopy, VecMove, FCountingElem::CopyCount, FCountingElem::MoveCount);
}

// ───────────────────────── 실험 4: 슬롯 주소 vs 객체 주소 ─────────────────────────

void AGcExperimentActor::Exp4_Prepare()
{
    Slots.Add(NewObject<UGcProbeData>(this));
    SlotAddrBefore = ToAddr(&Slots[0]);
    ObjAddrBefore = ToAddr(Slots[0].Get());

    for (int32 i = 0; i < GrowCount; ++i) { Slots.Add(NewObject<UGcProbeData>(this)); }

    UE_LOG(LogTemp, Display, TEXT("[EXP4] after Add | slot moved=%s | pointer value kept=%s"),
        BoolStr(SlotAddrBefore != ToAddr(&Slots[0])),
        BoolStr(ObjAddrBefore == ToAddr(Slots[0].Get())));
}

void AGcExperimentActor::Exp4_Verify()
{
    UE_LOG(LogTemp, Display, TEXT("[EXP4] verify    | object unchanged=%s"),
        BoolStr(ObjAddrBefore == ToAddr(Slots[0].Get())));
}

// ───────────────────────── 실험 5: 파괴된 액터 참조 ─────────────────────────

void AGcExperimentActor::Exp5_Prepare()
{
    AActor* Victim = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    VictimTracked = Victim;
    VictimArray.Add(Victim);
    VictimRaw = Victim;

    Victim->Destroy();

    UE_LOG(LogTemp, Display, TEXT("[EXP5] after Destroy | tracked null=%s | array[0] null=%s | raw null=%s"),
        BoolStr(VictimTracked == nullptr), BoolStr(VictimArray[0] == nullptr), BoolStr(VictimRaw == nullptr));
}

void AGcExperimentActor::Exp5_Verify()
{
    UE_LOG(LogTemp, Display, TEXT("[EXP5] verify        | tracked null=%s | array Num=%d | array[0] null=%s | raw null=%s"),
        BoolStr(VictimTracked == nullptr), VictimArray.Num(),
        BoolStr(VictimArray[0] == nullptr), BoolStr(VictimRaw == nullptr));
}
```

</details>

### 3.6 실험별 입력 · 출력 · 통과 조건

- GC 실험(1, 1b, 4, 5)은 `[GC] sentinel`의 `gc ran` 값을 먼저 확인한 뒤 판정함
- 실행 A에서 `gc ran=false`이면 GC 실험 결과는 판정하지 않고 재실행함
- 구체적인 `Max` 증가 값은 문서가 정하지 않은 할당자 동작이므로 판정 기준에서 제외함

| 실험 | 실행 | 입력                                                                                               | 확인 로그                            | 통과 조건                                                                                        | 근거                                                          |
| ---- | ---- | -------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| 1    | A    | `UPROPERTY` 객체 1개 + 참조 없는 객체 10,000개 → Full Purge GC                                     | `[EXP1] prepare`, `verify`, `result` | sentinel 0/10000, address unchanged / raw==tracked / same object 모두 true                       | GC 제거 대상[^4], 약한 포인터 null 반환[^6]                   |
| 1b   | A    | 객체 10,000개 생성, 10번째마다 `UPROPERTY` 배열에 보관 → Full Purge GC                             | `[EXP1b] prepare`, `verify`          | survivors moved 0/1000, garbage alive 0/9000                                                     | 압축 GC의 생존 객체 이동 방향[^1]                             |
| 2    | A, B | 빈 `TArray<int32>`에 1개 + 1,000개 추가 / 대조: `Reserve(1001)` 후 같은 작업                       | `[EXP2]` 3줄                         | before Max=4, after buffer moved=true, reserve buffer moved=false                                | Slack 설명[^7]                                                |
| 3    | A, B | 자기 주소를 기록하는 `FSelfRef`를 vector와 TArray에 각각 1,000개 추가                              | `[EXP3]`                             | vector 0/1000, TArray 1 이상                                                                     | 바이트 복사 가정[^7], vector 재할당[^8]                       |
| 3b   | A, B | `TArray<FSelfRef>`에 1,000개 추가하며 재할당마다 옮겨진 요소 수 기록                               | `[EXP3b]`                            | 첫 줄 moved=0, result match=true                                                                 | 실험 3의 해석 검증                                            |
| 3c   | A, B | 생성자 호출을 세는 `FCountingElem`을 vector와 TArray에 각각 1,000개 추가                           | `[EXP3c]`                            | vector copy=0 move 1 이상, TArray copy=0 move=0                                                  | 바이트 복사 가정[^7], vector 재할당[^8], destructive move[^9] |
| 4    | A    | `UPROPERTY TArray<TObjectPtr<>>`에 1개 + 1,000개 추가 → Full Purge GC                              | `[EXP4] after Add`, `verify`         | slot moved, pointer value kept, object unchanged 모두 true                                       | 실험 1과 2의 조합                                             |
| 5    | A    | 액터를 `UPROPERTY TObjectPtr`, `UPROPERTY TArray`, raw 포인터에 저장 → `Destroy()` → Full Purge GC | `[EXP5] after Destroy`, `verify`     | after Destroy 전부 false, verify tracked null true / Num 1 / array[0] null true / raw null false | 참조 자동 null 처리[^4]                                       |

#### 실행 B 판정 기준 (실험 5 대조군)

- 가설: "`UPROPERTY` 참조의 null 처리는 GC가 수행함"
- GC 실행 주기는 Project Settings의 **Time Between Purging Pending Kill Objects**로 조정함[^4]
- 강제 GC를 빼면, 대기 시간 안에 자동 GC가 돌지 않는 한 null 처리도 발생하지 않아야 함

| `[GC] sentinel` 결과      | `[EXP5] verify` 결과                                    | 판정                                                                             |
| ------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 10000/10000, gc ran=false | tracked null=false, array[0] null=false, raw null=false | 가설 지지                                                                        |
| 10000/10000, gc ran=false | tracked null=true                                       | 가설 기각 (GC 외의 경로로 null 처리됨)                                           |
| 0/10000, gc ran=true      | (무관)                                                  | 판정 불가: 자동 GC가 대기 중에 실행됨 → `VerifyDelaySeconds`를 0.5로 줄여 재실행 |
| 0과 10000 사이            | (무관)                                                  | 판정 불가: GC 진행 중 → 재실행                                                   |

- 실행 B에서는 GC가 돌지 않으므로 실험 1, 1b, 4의 `verify` 결과는 판정에서 제외함
- 실험 2, 3, 3b, 3c는 GC와 무관하므로 실행 B에서도 같은 결과가 나와야 함 (재현성 확인용)

## 4. 실험 1, 1b: GC는 살아 있는 UObject를 옮기는가

### 실험 1. 단일 객체 (실행 A)

- `UPROPERTY`로 붙잡은 객체 `Kept`와, GC가 모르는 raw 포인터 사본 `KeptRaw`를 함께 보관한 상태에서 Full Purge GC를 실행함

```cpp
Kept    = NewObject<UGcProbeData>(this);   // UPROPERTY → 도달 가능
KeptRaw = Kept.Get();                      // GC가 모르는 사본
for (int32 i = 0; i < 10000; ++i)          // 참조 없음 → 수거 대상 (GC 감시자)
    GarbageWeaks.Add(NewObject<UGcProbeData>(GetTransientPackage()));
```

| 지표                 | 의미                                   | 기댓값 | 실제 결과                               |
| -------------------- | -------------------------------------- | ------ | --------------------------------------- |
| `Kept` 주소          | GC 전후 주소 비교                      | 동일   | `000001C7787AB8C0` → `000001C7787AB8C0` |
| `address unchanged`  | 객체가 옮겨지지 않았는가               | true   | **true**                                |
| `raw==tracked`       | GC가 추적 참조만 몰래 고쳤는가         | true   | **true**                                |
| `same object(index)` | 같은 객체인가 (`GUObjectArray` 인덱스) | true   | **true** (68963 → 68963)                |

- `raw==tracked`가 핵심 지표임
- GC가 객체를 옮기고 추적 참조(`UPROPERTY`)만 새 주소로 고쳤다면, GC가 모르는 `KeptRaw`는 옛 주소에 남아 false가 나와야 함

<!-- TODO: 05.png — 실행 A, Output Log 필터 "[EXP1]" : prepare, verify, result 줄 캡쳐 -->
![실행 A의 실험 1 로그](/assets/images/2026-10-08-ue5_gc/05.png)
_그림 7. 실행 A, 실험 1 — `prepare`, `verify`, `result`_

### 실험 1b. 쓰레기 사이에 끼운 생존 객체 (실행 A)

- 실험 1의 `Kept`는 쓰레기보다 먼저 생성한 객체임
- 압축 GC는 생존 객체를 세그먼트의 오래된 쪽 끝으로 옮기므로[^1], 가장 먼저 만든 객체는 압축 GC에서도 이동하지 않았을 가능성이 존재함
- 이 가능성을 배제하기 위해 쓰레기 9개마다 생존 객체 1개를 끼워 넣어, 모든 생존 객체 앞에 해제될 구멍이 생기도록 배치함
- 그림 8은 생성 순서 개념도이며, 실제 메모리 주소 배치는 할당자가 결정함

![실험 1b 생존 객체 배치 개념도](/assets/images/2026-10-08-ue5_gc/19.png)
_그림 8. 쓰레기 9개 다음에 생존 객체 1개를 두는 패턴을 1,000번 반복함_

```cpp
for (int32 i = 0; i < 10000; ++i)
{
    UGcProbeData* Obj = NewObject<UGcProbeData>(GetTransientPackage());
    if (i % 10 == 9) { Survivors.Add(Obj); SurvivorAddrBefore.Add(ToAddr(Obj)); }  // UPROPERTY 배열
    else             { InterleavedGarbage.Add(Obj); }                            // 약한 포인터
}
```

| 지표                        | 기댓값      | 실제 결과        |
| --------------------------- | ----------- | ---------------- |
| GC 전 생존 객체 / 쓰레기    | 1000 / 9000 | 1000 / 9000/9000 |
| GC 후 쓰레기 생존           | 0/9000      | **0/9000**       |
| GC 후 주소가 바뀐 생존 객체 | 0/1000      | **0/1000**       |

<!-- TODO: 06.png — 실행 A, Output Log 필터 "[EXP1b]" : prepare, verify 줄 캡쳐 -->
![실행 A의 실험 1b 로그](/assets/images/2026-10-08-ue5_gc/06.png)
_그림 9. 실행 A, 실험 1b — `prepare`, `verify`_

- GC는 쓰레기 9,000개를 모두 수거함
- 그 사이에 있던 생존 객체 1,000개 중 주소가 바뀐 객체는 0개임

## 5. 실험 5: 파괴된 객체의 참조는 언제 null이 되는가

- 주소 유지는 객체가 살아 있는 동안에 한정된 결과임
- 객체 파괴 후의 참조 상태를 실행 A와 B로 비교함

```cpp
VictimTracked = Victim;    // UPROPERTY TObjectPtr
VictimArray.Add(Victim);   // UPROPERTY TArray
VictimRaw     = Victim;    // raw 포인터 (비교만, 역참조 금지)
Victim->Destroy();
```

| 시점             | 지표                          | 실행 A (강제 GC)      | 실행 B (GC 없음)        |
| ---------------- | ----------------------------- | --------------------- | ----------------------- |
| `Destroy()` 직후 | tracked / array[0] / raw null | false / false / false | false / false / false   |
| 2초 후           | GC 감시자                     | 0/10000 (GC 실행)     | 10000/10000 (GC 미실행) |
| 2초 후           | tracked null                  | **true**              | **false**               |
| 2초 후           | array Num / array[0] null     | 1 / **true**          | 1 / **false**           |
| 2초 후           | raw null                      | false                 | false                   |

![실험 5 실행 A와 B의 null 처리 시점](/assets/images/2026-10-08-ue5_gc/07.png)
_그림 10. 두 실행의 차이는 GC 실행 여부뿐임_

<!-- TODO: 08.png — 실행 A, Output Log 필터 "[EXP5]" : after Destroy, verify 줄 캡쳐 -->
![실행 A의 실험 5 로그](/assets/images/2026-10-08-ue5_gc/08.png)
_그림 11. 실행 A, 실험 5 — `after Destroy`, `verify`_

<!-- TODO: 09.png — 실행 B, Output Log 필터 "[EXP5]" : after Destroy, verify 줄 캡쳐 -->
![실행 B의 실험 5 로그](/assets/images/2026-10-08-ue5_gc/09.png)
_그림 12. 실행 B, 실험 5 — `after Destroy`, `verify`_

- 두 실행의 차이는 GC 실행 여부 하나뿐임
- 확인 사항:
  1. `UPROPERTY` 참조(단일 포인터, `TArray` 요소 모두)가 `Destroy()` 직후가 아니라 GC 실행 후에 null로 바뀐 것을 확인함. `TArray`는 요소 수를 유지하고 값만 null임 (`Num=1`)
  2. raw 포인터는 GC 후에도 null이 아님. 파괴된 객체의 옛 주소를 그대로 보유한 댕글링 포인터임
  3. `Destroy()` 후 GC 전까지는 `UPROPERTY` 참조도 null이 아님. null 체크만으로는 `Destroy()` 여부 판단이 불가함

## 6. 실험 2: TArray는 자기 버퍼를 옮김

- GC는 UObject를 옮기지 않지만, `TArray`는 자기 버퍼를 재할당함
- `TArray` 할당자는 요소 추가 시마다 재할당하지 않도록 요청보다 많은 메모리를 확보함[^7]
- `GetData()`가 반환한 포인터는 배열이 존재하고 변경 연산이 일어나기 전까지만 유효함[^7]
- `std::vector`도 `push_back` 후 새 크기가 기존 용량을 넘으면 재할당하며, 이때 모든 이터레이터와 요소 참조를 무효화함[^8]

![TArray 버퍼 재할당과 댕글링 포인터](/assets/images/2026-10-08-ue5_gc/10.png)
_그림 13. 재할당 후 미리 저장한 포인터 P는 해제된 옛 버퍼를 가리킴 (주소 값은 예시)_

```cpp
TArray<int32> Arr;
Arr.Add(0);                                      // Num=1
const UPTRINT Before = ToAddr(Arr.GetData());    // 주소만 기록 (역참조 금지)
for (int32 i = 1; i <= 1000; ++i) Arr.Add(i);    // 용량 초과 → 재할당

TArray<int32> Reserved;
Reserved.Reserve(1001);                          // 대조군: 슬랙을 미리 확보
```

| 경우                         | 기댓값                                    | 실제 결과 (실행 A, B 동일)                 |
| ---------------------------- | ----------------------------------------- | ------------------------------------------ |
| 첫 `Add` 직후                | Num=1, Max=4 (문서 Slack 예시와 동일)[^7] | **Num=1, Max=4**                           |
| 1,000개 추가 후              | Num=1001, buffer moved=true               | **Num=1001, Max=1139, buffer moved=true**  |
| `Reserve(1001)` 후 같은 작업 | buffer moved=false                        | **Num=1001, Max=1001, buffer moved=false** |

<!-- TODO: 11.png — 실행 A, Output Log 필터 "[EXP2]" : grow before, grow after, reserve 줄 캡쳐 -->
![실행 A의 실험 2 로그](/assets/images/2026-10-08-ue5_gc/11.png)
_그림 14. 실행 A, 실험 2 — `grow before`, `grow after`, `reserve`_

- 1,000개 추가 중 버퍼가 다른 주소로 이동함
- 처음 저장한 `Before` 주소는 이미 해제된 버퍼를 가리키며, 이 주소로 접근하면 UB임
- `Reserve`로 슬랙을 미리 확보하면 같은 1,000개를 추가해도 버퍼를 유지함
- `Max=1139`는 문서가 정하지 않은 할당자 동작이므로 관찰값으로만 기록함

## 7. 실험 3, 3b, 3c: TArray는 요소를 '바이트 복사'로 옮김

- `TArray`는 요소 타입이 trivially relocatable하다고 가정함. 즉 원시 바이트 복사로 요소를 옮겨도 안전하다고 간주함[^7]
- 재배치를 담당하는 `RelocateConstructItems`는 이 동작을 C++에 단일 연산이 없는 'destructive move'로 설명함[^9]
- `std::vector`는 재할당 시 요소의 move 생성자를 사용함[^8]
- 실험 3에서 현상을 확인하고, 실험 3b에서 깨진 요소를 특정하고, 실험 3c에서 원인을 확인하는 순서로 진행함

### 실험 3. 재할당 후 자기 포인터가 깨지는가

- 생성될 때 자기 주소를 `Self`에 기록하는 타입을 `std::vector`와 `TArray`에 각각 1,000개 추가함
- 생성자를 거쳐 옮겨지면 `Self == this`, 바이트 복사로 옮겨지면 옛 주소가 남아 `Self != this`임

```cpp
struct FSelfRef
{
    const FSelfRef* Self;
    FSelfRef() : Self(this) {}
    FSelfRef(const FSelfRef&) : Self(this) {}
    FSelfRef(FSelfRef&&) noexcept : Self(this) {}
    bool IsIntact() const { return Self == this; }
};
```

| 컨테이너      | 기댓값 (깨진 요소 수) | 실제 결과 (실행 A, B 동일) |
| ------------- | --------------------- | -------------------------- |
| `std::vector` | 0/1000                | **0/1000**                 |
| `TArray`      | 1 이상/1000           | **816/1000**               |

<!-- TODO: 13.png — 실행 A, Output Log 필터 "[EXP3]" : self-pointer broken 줄 캡쳐 -->
![실행 A의 실험 3 로그](/assets/images/2026-10-08-ue5_gc/13.png)
_그림 15. 실행 A, 실험 3 — `self-pointer broken`_

- `std::vector`의 요소는 1,000개 모두 정상임
- `TArray`는 1,000개 중 816개의 `Self`가 자기 주소가 아닌 옛 주소를 가리킴

### 실험 3b. 어떤 요소가 깨졌는가

- `TArray<FSelfRef>`에 1,000개를 추가하면서, 버퍼 주소가 바뀔 때마다 그 시점에 이미 존재하던 요소 수를 기록함
- 마지막 재할당에서 옮겨진 요소 수가 깨진 요소 수와 같으면, "재할당 때 바이트 복사로 옮겨진 요소만 깨졌다"는 해석이 성립함

```cpp
const int32 ExistingBefore = Arr.Num();
Arr.Emplace();
if (ToAddr(Arr.GetData()) != LastData)   // 버퍼 주소가 바뀌면 재할당으로 판단
{
    LastData       = ToAddr(Arr.GetData());
    LastMovedCount = ExistingBefore;      // 이번 재할당에서 옮겨진 요소 수
}
```

| 지표           | 기댓값                | 실제 결과 (실행 A, B 동일)                 |
| -------------- | --------------------- | ------------------------------------------ |
| 첫 버퍼 할당   | `Num 0 -> 1`, moved=0 | **`Num 0 -> 1`, Max=4, moved=0**           |
| 버퍼 할당 횟수 | (관찰값)              | **11회** (최초 할당 포함)                  |
| 마지막 재할당  | (관찰값)              | **`Num 816 -> 817`, Max=1139, moved=816**  |
| result         | match=true            | **last moved=816, broken=816, match=true** |

<!-- TODO: 14.png — 실행 A, Output Log 필터 "[EXP3b]" : realloc 11줄과 result 줄 캡쳐 -->
![실행 A의 실험 3b 로그](/assets/images/2026-10-08-ue5_gc/14.png)
_그림 16. 실행 A, 실험 3b — `realloc` 11줄과 `result`_

- 실험 3b로 816의 의미를 확인함
- 마지막 재할당(`Num 816 → 817`) 시점에 존재하던 816개는 바이트 복사로 이동해 `Self`가 옛 주소를 가리킴
- 이후 새 버퍼에서 바로 생성된 184개만 정상임
- 재할당 시점의 `Max` 값은 문서가 정하지 않은 할당자 동작이므로 관찰값으로만 기록함

![실험 3과 3b 결과: 깨진 요소 816개](/assets/images/2026-10-08-ue5_gc/15.png)
_그림 17. 마지막 재할당 때 존재하던 816개만 깨짐_

### 실험 3c. 왜 깨졌는가: 재할당 중 생성자 호출 0회

- 복사/이동 생성자 호출을 세는 타입을 `std::vector`와 `TArray`에 각각 1,000개 추가함
- 요소는 `emplace_back`/`Emplace`로 제자리 생성하므로, 집계된 호출은 전부 재할당 때문에 발생한 것임

```cpp
struct FCountingElem
{
    inline static int32 CopyCount = 0, MoveCount = 0;
    FCountingElem() = default;
    FCountingElem(const FCountingElem&)     { ++CopyCount; }
    FCountingElem(FCountingElem&&) noexcept { ++MoveCount; }
};
```

| 컨테이너      | 기댓값         | 실제 결과 (실행 A, B 동일) |
| ------------- | -------------- | -------------------------- |
| `std::vector` | copy=0, move≥1 | **copy=0, move=2137**      |
| `TArray`      | copy=0, move=0 | **copy=0, move=0**         |

<!-- TODO: 12.png — 실행 A, Output Log 필터 "[EXP3c]" : ctor calls 줄 캡쳐 -->
![실행 A의 실험 3c 로그](/assets/images/2026-10-08-ue5_gc/12.png)
_그림 18. 실행 A, 실험 3c — `ctor calls`_

- `TArray`는 실험 3b에서 확인한 여러 번의 재할당 동안 복사/이동 생성자 호출이 0회임
- `std::vector`는 move 생성자만 사용했고 복사는 0회임
- move 횟수 2137은 이 환경의 `std::vector` 성장 정책에 따른 관찰값임

## 8. 실험 4: 움직이는 것은 '슬롯', 움직이지 않는 것은 '객체'

- `UPROPERTY TArray<TObjectPtr<UGcProbeData>>`에서 배열 칸(슬롯)의 주소와 칸 안 객체의 주소를 따로 추적함

![TArray 슬롯 버퍼와 UObject 객체의 분리](/assets/images/2026-10-08-ue5_gc/16.png)
_그림 19. 슬롯은 재할당으로 이동하고, 객체는 GC 후에도 제자리에 있음_

```cpp
Slots.Add(NewObject<UGcProbeData>(this));
SlotAddrBefore = ToAddr(&Slots[0]);        // 슬롯(배열 칸)의 주소
ObjAddrBefore  = ToAddr(Slots[0].Get());   // 슬롯이 가리키는 객체의 주소
for (int32 i = 0; i < 1000; ++i)           // 재할당 유발
    Slots.Add(NewObject<UGcProbeData>(this));
// 이후 Full Purge GC
```

| 시점            | 지표                 | 의미                                         | 기댓값 | 실제 결과 (실행 A) |
| --------------- | -------------------- | -------------------------------------------- | ------ | ------------------ |
| 1,000개 추가 후 | `slot moved`         | 배열 칸이 재할당으로 이동했는가              | true   | **true**           |
| 1,000개 추가 후 | `pointer value kept` | 이동한 칸 안의 포인터 값이 그대로 복사됐는가 | true   | **true**           |
| GC 후           | `object unchanged`   | GC를 거쳐도 객체 주소가 그대로인가           | true   | **true**           |

<!-- TODO: 17.png — 실행 A, Output Log 필터 "[EXP4]" : after Add, verify 줄 캡쳐 -->
![실행 A의 실험 4 로그](/assets/images/2026-10-08-ue5_gc/17.png)
_그림 20. 실행 A, 실험 4 — `after Add`, `verify`_

- **슬롯 주소**(`&Slots[0]`): `TArray` 재할당으로 댕글링이 발생함
- **슬롯 안의 값**(`Slots[0].Get()`): 배열 재할당과 GC를 모두 거쳐도 같은 객체 주소임
- 단, 객체가 **파괴**되면 raw 포인터로 꺼내 둔 값은 GC 후에도 null이 아님 (실험 5)

## 9. 안전 패턴

| 상황                               | 권장 방법                                                                          | 근거                                 |
| ---------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------ |
| 배열 요소 포인터를 잠깐 사용       | 변경 연산 전까지만 사용하고, 변경 후에는 다시 조회                                 | `GetData()` 유효 범위[^7], 실험 2    |
| 추가하는 동안 버퍼 유지            | `Reserve()`로 슬랙을 미리 확보                                                     | 슬랙 설명[^7], 실험 2 대조군         |
| 요소를 나중에 다시 찾기            | 요소 주소 대신 인덱스로 저장 후 재조회                                             | 실험 2, 4                            |
| 자기 참조 구조체를 `TArray`에 저장 | 내부 포인터를 두지 않는 설계 (오프셋/인덱스 사용)                                  | 바이트 복사 가정[^7], 실험 3, 3b, 3c |
| UObject를 오래 참조                | `UPROPERTY() TObjectPtr<>` 또는 `TWeakObjectPtr<>`                                 | 문서 권장[^4][^6], 실험 5            |
| 대상의 파괴 여부 확인              | null 체크만으로는 부족함. `Destroy()` 후 GC 전까지는 `UPROPERTY` 참조도 non-null임 | 실험 5 실행 B                        |

## 마치며

- **UE5 GC는 살아 있는 UObject를 옮기지 않음**: 쓰레기 9,000개를 수거하는 동안, 그 사이에 끼워 둔 생존 객체 1,000개 중 주소가 바뀐 객체는 0개임 (실험 1, 1b)
- **`TArray`는 자기 버퍼를 옮김**: 요소 주소는 재할당 한 번에 무효가 됨 (실험 2). 재할당 중 생성자 호출이 0회이므로 (실험 3c) 자기 참조 요소는 내부까지 깨짐 (실험 3, 3b)
- **움직이지 않는 것은 UObject이고, 움직이는 것은 그 포인터를 담은 배열 칸임** (실험 4)
- **파괴된 객체는 별개의 문제임**: `UPROPERTY` 참조는 GC 실행 시 null로 바뀌고, raw 포인터는 끝까지 null이 아님 (실험 5)

---

[^1]: Microsoft Learn, *Fundamentals of garbage collection*. 원문: "A relocating phase that updates the references to the objects that are compacted." <https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/fundamentals>

[^2]: Microsoft Learn, *fixed statement — C# reference*. 원문: "prevents the garbage collector from relocating a moveable variable" <https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/fixed>

[^3]: Epic Developer Community, *Knowledge Base: Garbage Collector Internals*. 원문: "a standard Mark & Sweep collector" <https://dev.epicgames.com/community/learning/knowledge-base/ePKR/unreal-engine-garbage-collector-internals>

[^4]: Epic Games, *Unreal Object Handling in Unreal Engine* — "Automatic Updating of References", "Garbage Collection" 절 (5.8 표기 페이지). 원문: "references to it that are visible to the reflection system … are automatically nulled" <https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-object-handling-in-unreal-engine>

[^5]: Epic Games, *FUObjectItem* API (UObject/UObjectArray.h). `Object` 멤버 설명 원문: "Pointer to the allocated object" <https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/CoreUObject/FUObjectItem>

[^6]: Epic Games, *FWeakObjectPtr* API (UObject/WeakObjectPtr.h). 원문: "It can return nullptr later if the object is garbage collected." <https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/CoreUObject/FWeakObjectPtr>

[^7]: Epic Games, *TArray: Arrays in Unreal Engine* (5.8 표기 페이지). 원문: "assumes that the element type is trivially relocatable" (Slack, Queries, Raw Memory 절 참고) <https://dev.epicgames.com/documentation/en-us/unreal-engine/array-containers-in-unreal-engine>

[^8]: cppreference, *std::vector::push_back*. 원문: "all iterators (including the end() iterator) and all references to the elements are invalidated" <https://en.cppreference.com/w/cpp/container/vector/push_back>

[^9]: Epic Games, *RelocateConstructItems* API (UE 5.5 표기, Templates/MemoryOps.h). 원문: "This is a so-called 'destructive move'" <https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Core/Templates/RelocateConstructItems?application_version=5.5>

[^10]: cppreference, *std::vector* — 멤버 함수 표와 Iterator invalidation 표. 원문: "Reallocations are usually costly operations in terms of performance." <https://en.cppreference.com/w/cpp/container/vector>