---
title: "[Project CM] 클라이언트 동기화를 위한 로딩 시퀀스 구현"
description: "ACMGameStateBase의 클라이언트 로딩 시퀀스 구조를 구현했습니다. 이 클래스는 게임 시작 시점에서 클라이언트 초기화 과정을 n단계로 분리해 관리하며, 모든 동기화 대상 컴포넌트가 준비된 뒤 순차적으로 로딩 이벤트를 브로드캐스트하는 로직을 가지고 있습니다."
date: 2025-10-29T10:55:16.233Z
tags: ["project cm","ue5"]
image:
  path: /assets/images/old/bd70a123-80c5-44c4-b779-6563b9b1f387-image.png
categories: [Project CM + Project Arc]
---
오늘은 `ACMGameStateBase`의 클라이언트 로딩 시퀀스 구조를 구현했습니다. 이 클래스는 게임 시작 시점에서 **클라이언트 초기화 과정을 n단계로 분리해 관리**하며, 모든 동기화 대상 컴포넌트가 준비된 뒤 순차적으로 로딩 이벤트를 브로드캐스트하는 로직을 가지고 있습니다.

---

## 구현 코드  
- `Source/CrimsonMoon/Public/Game/CMGameStateBase.h`  
- `Source/CrimsonMoon/Private/Game/CMGameStateBase.cpp`

---


## 핵심 요약  
- 클라이언트 로딩 시퀀스는 **3단계(OnLoadBegin → OnLoadUI → OnLoadCompleted)** 로 구성됨.  
- 각 단계는 **“다음 틱(next tick)”** 에 예약되어 순차적으로 브로드캐스트됨.  
- **“동기화 대상 컴포넌트(Synced Components)”** 들이 모두 준비되면 시퀀스가 시작됨.  
- 델리게이트는 **C++ 전용(`DECLARE_MULTICAST_DELEGATE`)** 으로 블루프린트 바인딩 불가.

---
## 구성 요소  

### 동기화 트래커  
- `SyncedComponentMap`: `TMap<FName, int8>` → 0: 미완료 / 1: 완료  
- `SyncedComponentCount`: 완료된 컴포넌트 수  
- `RegisterSyncedComponents()`: 초기 등록 (현재 `"PlayerController"` 1개만 포함)

### 시퀀스 이벤트 (C++ 전용 델리게이트)  
- `FOnLoadBegin OnLoadBegin`  
- `FOnLoadUI OnLoadUI`  
- `FOnLoadCompleted OnLoadCompleted`

---

## 제어 메서드  

| 메서드 | 설명 |
|--------|------|
| `NotifyComponentSynced(FName)` | 해당 컴포넌트 완료 처리 → 전체 완료 시 `StartClientLoadSequence()` 호출 |
| `StartClientLoadSequence()` | 다음 틱에 `HandleLoadBegin()` 예약 |
| `HandleLoadBegin()` | `OnLoadBegin.Broadcast()` → 다음 틱에 `HandleLoadUI()` |
| `HandleLoadUI()` | `OnLoadUI.Broadcast()` → 다음 틱에 `HandleLoadCompleted()` |
| `HandleLoadCompleted()` | `OnLoadCompleted.Broadcast()` |

---

## 동작 흐름  

```text
(모든 컴포넌트 완료)
   ↓
[NextTick] → OnLoadBegin
   ↓
[NextTick] → OnLoadUI
   ↓
[NextTick] → OnLoadCompleted
```

## 실적용
![](/assets/images/old/bd70a123-80c5-44c4-b779-6563b9b1f387-image.png)

Sync가 모두 완료된 후 차례대로 Load 메소드를 실행하는 것을 볼 수 있습니다.

## 마치며

이번 분석을 통해 ACMGameStateBase가 틱 단위로 분리된 로딩 시퀀스 제어 구조를 통해 안정적으로 초기화를 수행함을 확인했습니다. 다만, 중복 호출 방지·리셋 로직·블루프린트 연동 부분의 보완이 필요함을 느꼈습니다.