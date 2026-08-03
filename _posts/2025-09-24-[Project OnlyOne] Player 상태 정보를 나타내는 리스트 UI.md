---
title: "[Project OnlyOne] Player 상태 정보를 나타내는 리스트 UI"
description: "플레이어들의 닉네임/생존 여부/킬 수를 UI 목록으로 표시하고, 게임 로직 변화에 따라 UI를 느슨 결합으로 갱신하는 것이 목표입니다."
date: 2025-09-24T11:15:18.826Z
tags: ["project onlyone","ue5"]
image:
  path: /assets/images/old/b5f5337b-09db-4a3e-9e8c-55ab9daa8a9c-image.webp
categories: [Project OnlyOne]
---
![](/assets/images/old/b5f5337b-09db-4a3e-9e8c-55ab9daa8a9c-image.webp)

## 1) 구현 개요
- 목표: 플레이어들의 닉네임/생존 여부/킬 수를 UI 목록으로 표시하고, 게임 로직 변화에 따라 UI를 느슨 결합으로 갱신.
- 핵심 아이디어: PlayerController에 멀티캐스트 델리게이트(FPOOnSetPlayerStateEntry)를 두고, 목록 UI 위젯(UPOPlayerStateListWidget)이 이를 구독해 변경 이벤트를 수신.
- 흐름: 게임 로직 → OnSetPlayerStateEntry.Broadcast → UPOPlayerStateListWidget::SetPlayerStateEntry → 항목 위젯(UPOPlayerStateElementWidget) 갱신.

## 2) 구성 요소와 책임
- APOPlayerController
  - 델리게이트 선언/소유: FPOOnSetPlayerStateEntry OnSetPlayerStateEntry
  - UI 클래스/인스턴스 보유: PlayerStateListWidgetClass, PlayerStateListWidget
  - 비고: 현 시점에 Broadcast 호출 지점은 프로젝트 내 미구현(추가 필요)

- UPOPlayerStateListWidget
  - 생명주기: NativeConstruct에서 델리게이트 바인딩(AddUObject), NativeDestruct에서 RemoveAll로 해제
  - 데이터 구조: TMap<FString, UPOPlayerStateElementWidget*>로 닉네임 키 기반 중복 방지
  - 주요 함수:
    - SetPlayerStateEntry(Nickname, bIsAlive, KillCount): 신규 항목 생성/기존 항목 갱신
    - ClearPlayerStateEntries(): 스크롤박스 자식 및 맵 비우기
  - UMG 연동: BindWidget된 ScrollBox(PlayerList), 에디터에서 PlayerEntryClass 지정 필요
  - 데모: NativeConstruct 말미에 더미 데이터 3건 추가(실사용 시 제거 권장)

- UPOPlayerStateElementWidget
  - 바인딩 위젯: NicknameText, AliveStateText, KillCountText (UTextBlock)
  - 값 캐싱: 생성 전 호출 대비를 위해 캐시 후 NativeConstruct에서 Apply
  - 표시 로직: 생존 true → " "(빈 문자열), false → "DEAD"

## 3) 델리게이트 사용 설계
- 선언(POPlayerController.h)
```cpp
DECLARE_MULTICAST_DELEGATE_ThreeParams(FPOOnSetPlayerStateEntry, const FString& /*Nickname*/, bool /*bIsAlive*/, int32 /*KillCount*/);
FPOOnSetPlayerStateEntry OnSetPlayerStateEntry;
```
  - 컨트롤러 멤버: 
- 구독/해제(UPOPlayerStateListWidget)
  - 구독: NativeConstruct에서 `AddUObject(this, &UPOPlayerStateListWidget::SetPlayerStateEntry)`
  - 중복 방지: `IsBoundToObject(this)` 체크 후 바인딩
  - 해제: NativeDestruct에서 `RemoveAll(this)`
- 브로드캐스트(추가 필요)
  - 게임 이벤트(사망/킬 증가/입퇴장 등)에서 컨트롤러 컨텍스트에서 호출
  - 예시:

```cpp
// 예: 플레이어 상태 변화 시(클라이언트 컨트롤러 컨텍스트)
if (APOPlayerController* PC = GetController<APOPlayerController>())
{
    PC->OnSetPlayerStateEntry.Broadcast(Nickname, bAlive, KillCount);
}
```

## 4) 인스턴스 간 통신 흐름
1) 게임 로직(예: 킬/사망 처리, 합류/퇴장)에서 데이터 변경 발생
2) APOPlayerController의 OnSetPlayerStateEntry.Broadcast(Nickname, bAlive, Kills)
3) 구독자 UPOPlayerStateListWidget가 SetPlayerStateEntry 호출됨
4) 해당 닉네임 항목 위젯(UPOPlayerStateElementWidget) 생성 또는 갱신 → UI 반영

장점: UI와 게임 로직의 느슨한 결합, 다중 구독자 지원, 테스트/대체 용이


## 5) 테스트
- 현재 더미 데이터가 NativeConstruct에서 3건 추가됨 → 위젯 로드 시 목록 채워지는지 확인
- 실제 이벤트 연동 전까지 임시로 임의 지점에서 Broadcast를 호출해 UI 반응 확인
- 완료 후 더미 데이터는 제거



