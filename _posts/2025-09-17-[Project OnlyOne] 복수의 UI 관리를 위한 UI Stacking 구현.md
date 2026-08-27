---
title: "[Project OnlyOne] 복수의 UI 관리를 위한 UI Stacking 구현"
description: "UI를 개발하다 보면 팝업, 모달, 서브메뉴가 겹겹이 뜨는 상황이 잦습니다. 사용자는 뒤로 가기(Back) 한 번으로 직전 화면으로 자연스럽게 돌아가길 기대하고, 개발자는 입력 차단과 포커스, 가시성, 수명을 일관되게 관리해야 합니다."
date: 2025-09-17T11:19:49.981Z
tags: ["project onlyone","ue5"]
image:
  path: /assets/images/old/19f3ae07-2c4f-440e-b5b5-65d73d9accad-image.webp
categories: [Project, Project OnlyOne]
---
![](/assets/images/old/19f3ae07-2c4f-440e-b5b5-65d73d9accad-image.webp)

UI를 개발하다 보면 팝업, 모달, 서브메뉴가 겹겹이 뜨는 상황이 잦습니다. 사용자는 뒤로 가기(Back) 한 번으로 직전 화면으로 자연스럽게 돌아가길 기대하고, 개발자는 입력 차단과 포커스, 가시성, 수명을 일관되게 관리해야 합니다. 이 글은 Unreal Engine UMG 환경에서 PlayerController 소유 컴포넌트가 UUserWidget의 수명·입력·가시성을 스택으로 관리하는 방식과, 그로부터 얻는 실전적 이점을 설명합니다.


# 왜 스택인가

스택은 “마지막에 올린 위젯이 최상단에서 보인다”라는 단순한 규칙으로 복잡한 UI 전환을 정리합니다. 새 위젯을 푸시하면 기존 최상단은 접고(Collapsed) 새 위젯만 보이게 하며, 팝으로 되돌릴 때는 직전 상태가 자동으로 복원됩니다. 최초 진입 시에는 `FInputModeUIOnly`로 입력을 전환하고 마우스 커서를 켜서 게임 조작과 분리합니다. 가시성은 새 위젯을 Visible, 바로 아래 위젯을 Collapsed로 두어 렌더·히트테스트·레이아웃 비용을 줄입니다. 수명은 `AddToViewport`와 `RemoveFromParent` 시점을 명확히 규정해 누락과 중복을 방지합니다.

>
- 스택 기반 관리: 최근에 푸시한 위젯이 최상단이 되며, 기존 최상단은 자동으로 접기(Collapsed)
- 첫 진입 시 입력 전환: 최초 Push 시 FInputModeUIOnly + 마우스 커서 On → 게임 조작과 분리
- 가시성 전환 최소화: 새 위젯은 Visible, 직전 위젯은 Collapsed로 레이아웃/히트테스트 비용을 줄임
- 명시적 수명 제어: AddToViewport 시점과 Pop 시 RemoveFromParent 시점을 일관되게 관리(권장)

# 핵심 동작 요약
- PushWidget(UUserWidget*):
  - nullptr 방지 체크
  - 기존 최상단 위젯 SetVisibility(Collapsed)
  - 스택이 비어있다면: PlayerController 입력을 FInputModeUIOnly, bShowMouseCursor = true
  - 새 위젯 AddToViewport, SetVisibility(Visible), 스택에 Push
- PopWidget():
  - 스택이 비어있으면 무시
  - 최상단 위젯을 RemoveFromParent 후 스택 Pop
  - 남은 새 최상단 위젯이 있다면 SetVisibility(Visible)
  - 스택이 비면 입력을 게임으로 복귀(FInputModeGameOnly 또는 GameAndUI), 커서 Off

# 장점
- 일관된 사용자 경험: 모달/팝업/서브메뉴를 단일 규칙으로 관리, Back 동작이 자연스럽고 예측 가능
- 입력 안전성: UI가 열릴 때 게임 입력 차단, 닫힐 때 자동 복귀 → 오입력/중복 입력 방지
- 성능/비용 최적화: 하위 위젯 Collapsed로 렌더·히트테스트·레이아웃 비용 감소
- 유지보수 용이: 화면 전환 로직이 Push/Pop 두 API로 수렴 → 블루프린트/코드 양과 복잡도 감소
- 확장성: 애니메이션, 사운드, 포커스, 접근성(키보드/패드) 정책을 중앙에서 일괄 적용 가능

# 엣지 케이스와 대응
- 스택 비어있는 상태에서 Pop 호출: 무시 안전 처리
- 최초 Push 이전/이후 입력 모드 전환 누락: 조건 분기(스택 empty ↔ non-empty)로 엄격 관리
- 위젯이 외부에서 RemoveFromParent된 경우: 스택 실제 상태와 동기화(유효성 검사)
- 패드 전용 환경: GameAndUI + Focus 선점, 마우스 커서 On/Off 정책 프로젝트별 분기
- 애니메이션 지연: 비동기 닫기 중 연속 Pop 방지(리엔트런시 락)

# 간단 흐름 예시
- 메인 메뉴(Visible) → 설정(Visible, 메인 메뉴 Collapsed) → Pop → 메인 메뉴 자동 복귀(Visible)
- 팝업 연쇄: 인벤토리 → 상세 보기 → 확인 다이얼로그 → Pop×2로 순차 복귀

# 도입 효과
- UI 상태 전이의 버그율 감소(포커스/입력/가시성 누락 방지)
- 신기능 추가 속도 향상(팝업 추가 시 Push만 호출)
- QA/디자인 협업 개선(일관 규칙 기반 시나리오 테스트 용이)

# 마치며
UI를 스택으로 관리하면 최근 UI만 보이고 나머지는 접히며, 입력은 상황에 맞게 전환되는 일관된 사용자 경험을 제공합니다. Push/Pop이라는 단순한 인터페이스 위에 포커스, 입력, 애니메이션, 중복 방지 네 가지 보완을 얹으면 실서비스 품질을 안정적으로 달성할 수 있습니다.
