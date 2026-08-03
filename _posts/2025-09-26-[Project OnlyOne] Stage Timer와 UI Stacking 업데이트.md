---
title: "[Project OnlyOne] Stage Timer와 UI Stacking 업데이트"
description: "스테이지의 남은 시간을 출력하는 UI와 UI Stacking을 개선했습니다."
date: 2025-09-26T10:19:26.350Z
tags: ["Project OnlyOne","UE5"]
image:
  path: /assets/images/old/552f42f7-b1f3-474f-9a90-d7d98320b911-image.webp
categories: [Project OnlyOne]
---
## 1. StageTimerWidget

![](/assets/images/old/552f42f7-b1f3-474f-9a90-d7d98320b911-image.webp)
### 역할(Overview)
- APOStageGameState로부터 남은 스테이지 시간(초)을 받아 화면(TextBlock)에 즉시 + 실시간 업데이트.
- NativeConstruct: GameState 캐시 → 초기 값 적용 → OnStageTimeUpdated 델리게이트 바인딩.
- NativeDestruct: 델리게이트 해제(핸들 검사 후 Remove).

### 핵심 함수 흐름
1. **NativeConstruct()**
   - `GetWorld()->GetGameState<APOStageGameState>()` 레퍼런싱
   - `StageGameState->GetStageRemainingSeconds()`로 초기 표시
   - `StageGameState->OnStageTimeUpdated.AddUObject(...)` 바인드
2. **HandleStageTimeUpdated(int32 Seconds)**
   - 음수면 0 클램프 → `FormatTimeMMSS()`
   - StageTimeText->SetText()
3. **FormatTimeMMSS(int32 TotalSeconds)**
   - 분/초 계산 → "%02d:%02d" 형식 FString → FText 변환
4. **NativeDestruct()**
   - 델리게이트 제거

### 테스트 체크
- 생성 직후 표시 정확성
- 시간 0 도달 시 00:00 유지(음수 불가)
- 위젯 빠른 열고닫기 반복 메모리/크래시 없음
- GameState 미존재 상황은 skip

---

## 2. POUIStackingComponent Default Widget 추가
### 목적(Overview)
- UI 위젯을 스택 구조(LIFO)로 관리해 오버레이/모달 전환 단순화.
- **index 0 = Default Widget(항상 남는 베이스 HUD) 예약.**
- Push: 이전 Top Collapsed → 새 위젯 Visible & Viewport 추가.
- Pop: Top 제거 → 이전 위젯 Visible 복원.
- **ClearStack (현재 구현): 배열만 비움(UIStack.Empty()) → Viewport 상 실제 위젯 제거/입력 모드 복원 없음 (이전 문서 설명과 차이, 리팩터링 필요).**

### 주요 필드/플로우
- UIStack: TArray<TObjectPtr<UUserWidget>>; 생성자에서 Add(nullptr)로 공간 확보.
- bIsInputModeUIOnly: SetDefaultWidget에서 설정(입력 모드 정책 플래그).
- **SetDefaultWidget(Widget, bUIOnly): UIStack[0] 치환, bIsInputModeUIOnly 저장, (bUIOnly일 때) InputModeUIOnly 설정 후 AddToViewport & Visible.**
- PushWidget: 이전 Top Collapsed → AddToViewport → Visible.
- PopWidget: 가드 (IsEmpty || Num <= 1) 시 즉시 return. → Top Pop RemoveFromParent, 남은 Top Visible.
