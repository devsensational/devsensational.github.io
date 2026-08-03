---
title: "[Project OnlyOne] Kill Feed"
description: "킬/데스 이벤트가 발생할 때 화면 우측/상단 등에 일정 시간 표시 후 자동으로 사라지는 피드를 제공합니다."
date: 2025-09-25T10:58:31.438Z
tags: ["Project OnlyOne","UE5"]
thumbnail: /assets/images/old/cf23d8ab-f264-41e9-8ab7-18ceac18497c-image.webp
categories: [Project OnlyOne]
---
![](/assets/images/old/cf23d8ab-f264-41e9-8ab7-18ceac18497c-image.webp)

## 1) 구현 개요(Overview)
- 목표: 킬/데스 이벤트가 발생할 때 화면 우측/상단 등에 일정 시간 표시 후 자동으로 사라지는 피드 제공.
- 핵심 아이디어: 컨테이너 위젯이 ScrollBox에 항목 위젯을 동적으로 추가하고, KillFeedDuration 경과 후 제거.
- 데이터: KillerName, VictimName(필수), 필요시 무기/팀/아이콘 등 확장 가능.

## 2) 구성 요소(Components)
1) UPOKillFeedWidget (컨테이너)
- 보관: ScrollBox KillFeedList, 항목 클래스 KillFeedEntryClass, 표시 시간 KillFeedDuration
- 역할: 항목 생성/추가/제거 스케줄링, (선택) 자동 스크롤, 정렬 방향 제어
- 생명주기: NativeConstruct(초기화/테스트 피드), NativeDestruct(타이머 정리)

2) UPOKillFeedElementWidget (항목)
- 보관: UTextBlock* KillerText, VictimText
- 역할: 텍스트 바인딩, (선택) 페이드 아웃 애니메이션 처리
- 주의: 항목 스스로 AddToViewport를 호출하지 않는다(부모 컨테이너가 관리).

## 3) 동작 흐름(Sequence)
1. NativeConstruct
   - (에디터/디버그 전용) 주기적으로 더미 항목 추가하는 타이머 등록
2. AddKillFeedEntry
   - 항목 위젯 생성 → 텍스트 바인딩 → ScrollBox에 AddChild(또는 InsertChildAt(0)) → 제거 타이머 등록
3. 제거 시점
   - 타이머 콜백에서 ScrollBox에서 제거(필요시 애니메이션 완료 후 제거)
4. NativeDestruct
   - 등록된 타이머 모두 정리

## 4) 테스트 플랜
- 기본: 이벤트 추가 후 KillFeedDuration 경과 시 정상 제거 확인(유령 위젯/누수 없음)
- 파괴 안전성: 위젯 열고 즉시 닫기 반복, 크래시 없음 확인
- 대량: 100개 연속 삽입 시 스크롤/프레임 유지
- 빌드 가드: Shipping 빌드에서 더미 타이머 미작동 확인
- UX: 상단 삽입/자동 스크롤/페이드아웃 동작 여부