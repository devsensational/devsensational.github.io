---
title: "[Project OnlyOne] Player State List UI의 동기화 문제 해결"
description: "Player State List는 'Tab'키를 누르면 해당 세션에 참가 중인 플레이어들의 생존 상태의 킬 스코어를 알려주는 UI입니다. 구현 후 실제 게임에 적용해보니, 인스턴스 초기화 시점과 Player State 동기화 시점이 달라 문제가 발생했습니다."
date: 2025-09-29T09:50:50.752Z
tags: ["Project OnlyOne","UE5","트러블슈팅"]
image:
  path: /assets/images/old/de92ec30-ec9b-42f0-941f-8824ac2749ca-image.png
categories: [Project OnlyOne]
---
![](/assets/images/old/de92ec30-ec9b-42f0-941f-8824ac2749ca-image.png)

Player State List는 'Tab'키를 누르면 해당 세션에 참가 중인 플레이어들의 생존 상태의 킬 스코어를 알려주는 UI입니다. 구현 후 실제 게임에 적용해보니, 인스턴스 초기화 시점과 Player State 동기화 시점이 달라 문제가 발생했습니다.

## 원인 분석
먼저 UI에 처음 등록되는 유저들의 정보가 추가되는 시점은 PlayerState가 초기화될 때입니다. 그리고 PlayerController의 Delegate에 Broadcast하면서, UI에 추가되게 됩니다. 따라서, 처음에는 PlayerController의 생성자 시점에서 UI Widget을 생성하면 해결될 것이라고 생각했습니다. 하지만 해결되지 않았고, **시행착오를 거치면서 PlayerState가 게임이 시작되기 전인 Lobby에서도 생성되었다는 점, ServerTravel이 수행되면서, 해당 PlayerState가 유지되면서 초기화가 일어나지 않았다는 것을 알게 되었습니다.**

## 문제 정의
| 문제 | 설명 | 결과적 위험 |
|------|------|-------------|
| 위젯 미생성 | 아직 `CreateWidget` 호출 전 | 이벤트 무시/유실 가능 |
| Slate 미구성 | `CreateWidget` 했지만 `AddToViewport` 이전 | 바인딩 위젯 접근/갱신 불안정 |
| 비가시 상태 | Collapsed / Hidden 상태 동안 이벤트 발생 | 표시 순간 UI와 실제 게임 상태 불일치 |


## 해결 방법
Tab 키로 열고 닫는 PlayerState 리스트(UI)가 "초기화되기 전" 또는 "숨김 상태" 동안 발생한 PlayerState 변화(생존/사망, 킬 수)를 잃지 않고, 최초 또는 재표시 시 순차적으로 반영하기 위해 `TQueue` 기반 지연 적용 전략을 사용했습니다. 이는 위젯 생성/표시 시점과 게임 플레이/네트워크 이벤트 도착 시점의 비동기를 느슨하게 결합하는 목적을 가집니다.

## 구현 핵심 (POPlayerController.cpp)
```cpp
OnSetPlayerStateEntry.AddUObject(this, &ThisClass::OnPlayerStateUpdated);
```
- 컨트롤러는 매우 이른 시점부터 상태 변경 이벤트 수신 가능.

Queue 처리 로직 요약:
```cpp
void APOPlayerController::OnPlayerStateUpdated(const FString& Nickname, bool bIsAlive, int32 KillCount)
{
    FPOPlayerStateEntry Entry{Nickname, bIsAlive, KillCount};
    if (PlayerStateListWidget && PlayerStateListWidget->IsInViewport() && PlayerStateListWidget->GetVisibility() == ESlateVisibility::Visible)
    {
        PlayerStateListWidget->SetPlayerStateEntry(Nickname, bIsAlive, KillCount);
    }
    else
    {
        PlayerStateQueue.Enqueue(Entry); // 지연 저장
    }
}
```
Flush (표시) 시점:
```cpp
void APOPlayerController::ShowListWidget()
{
    EnsureListWidgetCreated();
    if (PlayerStateListWidget)
    {
        if (!PlayerStateListWidget->IsInViewport())
            PlayerStateListWidget->AddToViewport();
        if (!PlayerStateQueue.IsEmpty())
        {
            FPOPlayerStateEntry Entry;
            while (PlayerStateQueue.Dequeue(Entry))
            {
                PlayerStateListWidget->SetPlayerStateEntry(Entry.Nickname, Entry.bIsAlive, Entry.KillCount);
            }
        }
        PlayerStateListWidget->SetVisibility(ESlateVisibility::Visible);
    }
}
```

## 장점
- 이벤트 손실 방지 (Lazy Init 환경에서 안전)
- 순차성(FIFO) 보장 → 사용자 이해도 향상 (변화 흐름 그대로 재생)
- 구현 단순 (`TQueue` + 조건 분기)
- 위젯 생명주기와 네트워크 타이밍 분리로 결합도 감소

## 한계 / 리스크
| 항목 | 설명 | 영향 |
|------|------|------|
| 중복 갱신 | 동일 플레이어 다회 상태 변화 모두 재생 | 불필요한 UI 연속 업데이트 |
| 메모리 누적 | 오랜 시간 표시 안 하면 Queue 성장 | 극단적 상황 외 영향 미미 |
| 최신 상태만 필요 시 비효율 | 히스토리 전체 유지 → 최종 스냅샷만 필요할 때 과잉 | 최적화 여지 |


## 결론
Queue 기반 지연 적용으로 PlayerState 이벤트 손실 없이 표시 시점 일관성을 달성할 수 있었습니다. 하지만, 이벤트 양이 폭증하거나 "최신 상태만"이 중요해질 때는 비효율 적일 수 있다고 느꼈습니다.