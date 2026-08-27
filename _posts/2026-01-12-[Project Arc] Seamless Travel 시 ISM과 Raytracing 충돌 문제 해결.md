---
title: "[Project Arc] Seamless Travel 시 ISM과 Raytracing 충돌 문제 해결"
description: "프로젝트에 레이트레이싱을 적용한 뒤, 심리스 트래블 시 Instanced Static Mesh(ISM) 때문에 발생하던 크래시를 추적하고 해결한 과정을 정리해 두려고 합니다."
date: 2026-01-12T07:13:29.961Z
tags: ["project arc","ue5","troubleshooting"]
image:
  path: /assets/images/old/477dc0db-f45c-4834-acee-96837f0b17b8-image.png
categories: [Project, Project CM + Project Arc]
---
프로젝트에 레이트레이싱을 적용한 뒤, **심리스 트래블 시 Instanced Static Mesh(ISM) 때문에 발생하던 크래시**를 추적하고 해결한 과정을 정리해 두려고 합니다. 동일한 구조의 네트워크/멀티플레이 프로젝트에서 레이트레이싱을 켜면 비슷한 문제를 겪을 수 있기 때문에, 원인과 대응 패턴을 기억해 두면 좋겠다는 생각이 들었습니다.

---

## 문제 상황 정리

- 증상
  - 레이트레이싱 옵션을 활성화한 상태에서 **심리스 트래블(SeamlessTravel)** 을 수행하면 간헐적으로 게임이 크래시.
  - 에디터 PIE나 레이트레이싱 OFF 환경에서는 잘 동작.


- 크래시 로그 핵심 부분 (요약)
  - Assertion 실패:
    - `Array index out of bounds: 1 into an array of size 1`
  - 콜스택 상 중요한 함수:
    - `FInstancedStaticMeshSceneProxy::GetDynamicRayTracingInstances()`
    - `RayTracing::FDynamicRayTracingInstancesContext::GatherDynamicRayTracingInstances_Internal()`


  - 로그 일부:


    ```text
    Assertion failed: (Index >= 0) & (Index < ArrayNum)
    [File:...Array.h] [Line: 1067]
    Array index out of bounds: 1 into an array of size 1
    ...
    FInstancedStaticMeshSceneProxy::GetDynamicRayTracingInstances()
    RayTracing::FDynamicRayTracingInstancesContext::GatherDynamicRayTracingInstances_Internal()
    Crash in runnable thread Foreground Worker #1
    ```

- 로그에서 볼 수 있는 사실
  - 크래시가 **레이트레이싱용 인스턴스 수집 과정**(`GatherDynamicRayTracingInstances`)에서 발생.
  - 특히 `FInstancedStaticMeshSceneProxy::GetDynamicRayTracingInstances()` 내부에서 ISM 관련 배열 접근 시 **인덱스 범위가 꼬인 상태**.
  - 즉, **InstancedStaticMesh 의 내부 상태(인스턴스 배열)가 심리스 트래블 전후 과정에서 깨졌을 가능성**이 매우 높음.

---

## 원인 분석

- 전제
  - InstancedStaticMeshComponent(ISM)는 **각 월드(서버/클라)** 에 존재.
  - 레이트레이싱은 각 클라이언트의 **로컬 월드** 안에 있는 ISM/StaticMesh 를 기준으로 씬을 빌드.


- 추정 원인
  - 심리스 트래블 시, 이전 월드에서 사용하던 ISM 인스턴스들이 **완전히 정리되지 않은 상태**에서
    - 월드가 전환되거나, 레이트레이싱 씬이 갱신되면서
    - 내부 `PerInstanceRenderData` / 인스턴스 배열 크기 정보가 어긋난 상태로 참조되는 상황.
  - 그 결과, `FInstancedStaticMeshSceneProxy::GetDynamicRayTracingInstances()` 가
    - `ArrayNum == 1` 인 배열을 `Index == 1`로 접근하는 식의 **out-of-bounds 접근**을 시도하다가 Assert 에 걸림.


- 왜 심리스 트래블에서만 티가 났는지
  - 일반적인 레벨 로드(OpenLevel)에서는 월드와 렌더링 관련 리소스가 비교적 깨끗하게 재생성/파괴됨.
  - 심리스 트래블은 **플레이어 관련 객체(Controller, PlayerState 등)를 유지한 채 월드만 교체**하기 때문에
    - 일부 렌더링/ISM 관련 리소스가 **월드 전환 타이밍에 완전히 정리되지 않고 남는** 경우가 발생할 수 있음.
  - 특히 레이트레이싱은 별도의 동적 인스턴스 수집/관리 경로를 타기 때문에, 이런 내부 상태 꼬임이 Assert 로 바로 드러남.

---

## 해결 전략

- 목표
  - **심리스 트래블 직전/직후에 각 월드의 ISM 상태를 확실하게 정리**해서,
  - 레이트레이싱용 인스턴스 수집 시 깨진 데이터를 참조하지 않도록 만들기.


- 고려한 방향들
  1. ISM 을 소유한 액터의 `EndPlay` / `BeginDestroy` 에서 개별적으로 정리
     - 가장 이상적인 구조지만, 현재 프로젝트 규모 상 모든 ISM 사용처를 일일이 추적하기에는 비용이 큼.
  2. 월드 단위로 ISM 을 한 번에 정리하는 세이프가드 추가
     - 심리스 트래블 직후, **각 클라이언트의 PlayerController가 자신이 속한 월드에서 ISM을 한 번 전체 스캔하여 인스턴스를 비우는 방식**.


- 최종 선택
  - **2번 방식**을 우선 적용:
    - `ACMPlayerController::PostSeamlessTravel()` 을 오버라이드.
    - 로컬 컨트롤러 기준으로 월드의 모든 `UInstancedStaticMeshComponent` 를 순회하며 `ClearInstances()` 호출.
    - 이 작업 이후, 기존에 구현해둔 **캐릭터 재스폰 + 화면/사운드 페이드 인** 로직을 그대로 이어서 실행.

---

## 구현 상세

### 1. PlayerController 에서 PostSeamlessTravel 오버라이드

- 파일 위치
  - `Source/CrimsonMoon/Public/Controllers/CMPlayerController.h`
  - `Source/CrimsonMoon/Private/Controllers/CMPlayerController.cpp`


- 헤더에 오버라이드 선언 (이미 추가되어 있음)

  - `CMPlayerController.h` (클래스 내부):

    - `virtual void PostSeamlessTravel() override;`


- cpp 에 구현 (주요 부분만 발췌)

> 역할: 
> - 심리스 트래블 완료 후, **로컬 월드의 모든 ISM 인스턴스를 정리**
> - 그 다음, 캐릭터 재스폰 및 화면/사운드 페이드 인


```cpp
#include "Components/InstancedStaticMeshComponent.h"
#include "EngineUtils.h" // TActorIterator

void ACMPlayerController::PostSeamlessTravel()
{
    Super::PostSeamlessTravel();

    // 로컬 컨트롤러가 아닌 경우 아무 것도 하지 않음 (서버 전용 PC 등 제외)
    if (!IsLocalController())
    {
        return;
    }

    // 1) 로컬 월드의 모든 InstancedStaticMeshComponent 정리
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!IsValid(Actor))
            {
                continue;
            }

            TArray<UInstancedStaticMeshComponent*> ISMComponents;
            Actor->GetComponents<UInstancedStaticMeshComponent>(ISMComponents);

            for (UInstancedStaticMeshComponent* ISMComp : ISMComponents)
            {
                if (!ISMComp)
                {
                    continue;
                }

                // 레이트레이싱/충돌 문제를 방지하기 위해 모든 인스턴스를 제거
                ISMComp->ClearInstances();
                ISMComp->MarkRenderStateDirty();
            }
        }
    }

    // 2) 심리스 트래블 후 캐릭터 재스폰 요청 (기존 로직)
    NotifyServerPlayerReadyWithCharacter();
    
    // 3) 화면/사운드 페이드 인 (검정 → 정상, 기존 연출)
    if (PlayerCameraManager)
    {
        PlayerCameraManager->StartCameraFade(
            /*FromAlpha*/ 1.0f,
            /*ToAlpha*/   0.0f,
            /*Duration*/  1.0f,
            /*Color*/     FLinearColor::Black,
            /*bShouldFadeAudio*/ true,
            /*bHoldWhenFinished*/ false
        );
    }
}
```


### 2. 기존 연출/로직과의 연계

- 이미 `ACMPlayerController` 에서는 심리스 트래블 이후에 다음 작업을 하고 있었음
  - `NotifyServerPlayerReadyWithCharacter()`
    - 서버에 선택된 캐릭터 태그를 보내고, 새 Pawn 스폰 요청.
  - `StartCameraFade(1 → 0, bShouldFadeAudio=true)`
    - 심리스 트래블 이전에 화면/오디오를 페이드 아웃한 것에 대응하여,
    - 새 맵에서 화면과 소리를 다시 자연스럽게 살리는 연출.
    
 

- 이번 수정에서는 이 두 기능을 유지한 채, 그 **이전에 ISM 정리 로직을 끼워 넣는 형태**로 구현.

---

## 적용 결과 및 배운 점

이번 수정 이후, 레이트레이싱을 활성화한 빌드에서 심리스 트래블을 반복 테스트했을 때,
기존에 발생하던 `FInstancedStaticMeshSceneProxy::GetDynamicRayTracingInstances` 관련 Assert 크래시는 더 이상 재현되지 않았습니다.

물론 근본적으로는 **ISM 을 소유하는 각 액터가 자신의 라이프사이클에 맞춰 적절히 정리되도록 설계하는 것**이 가장 좋겠지만,
이번과 같이 레이트레이싱 + 심리스 트래블 조합에서 내부 상태 꼬임으로 인한 크래시가 발생할 때에는,

- 월드 단위로 ISM 을 한 번 "강제로" 정리해 주는 세이프가드를 추가하여
- RT/Physics 씬에 남아 있는 잘못된 인스턴스 데이터를 제거하는 것만으로도
- 실질적인 크래시 문제를 빠르게 완화할 수 있다는 점을 다시 확인하게 되었습니다.

앞으로는 ISM 을 대량으로 사용하는 시스템을 설계할 때,
- 멀티플레이/심리스 트래블,
- 레벨 스트리밍,
- 레이트레이싱/Physics 씬 빌드 타이밍
같은 요소까지 함께 고려해서 **"누가 언제 ISM 을 생성/정리할 것인가"** 를 처음부터 명확히 정리해 두는 것이 중요하다는 것을 배웠습니다.

