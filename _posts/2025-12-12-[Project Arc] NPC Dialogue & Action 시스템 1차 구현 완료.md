---
title: "[Project Arc] NPC Dialogue & Action 시스템 1차 구현 완료"
description: "이번 작업에서는 CrimsonMoon 프로젝트에 NPC 대화(Npc Dialogue) 시스템을 1차적으로 구현하고, 위젯/액터/게임 인스턴스/로컬 이벤트 매니저 간의 구조를 정리하여 구현하였습니다."
date: 2025-12-12T11:42:19.112Z
tags: ["project arc","ue5"]
image:
  path: /assets/images/old/545204d6-1e33-4a75-8639-caa08ec17f7a-image.webp
categories: [Project CM + Project Arc]
---
이번 작업에서는 CrimsonMoon 프로젝트에 NPC 대화(Npc Dialogue) 시스템을 1차적으로 구현하고, 위젯/액터/게임 인스턴스/로컬 이벤트 매니저 간의 구조를 정리하여 구현하였습니다. 특히, C++과 UMG를 섞어 쓰는 환경에서 **델리게이트 기반 이벤트 흐름**과 **위젯/액터 간 의존성 최소화**를 목표로 진행했습니다.

---

## 전체 구조 개요
- 목표
  - NPC와 상호작용 시 대화 UI 표시
  - Next 버튼으로 다음 노드 진행
  - Action 노드가 있을 경우 선택지 버튼 동적 생성
  - 선택지 클릭 시 해당 액션 타입으로 NPC 컴포넌트 동작 수행
  - 대화 종료 시 델리게이트/상태 정리
- 핵심 구성 요소
  - `ACMNpcBase` : NPC 액터, 대화 트리 데이터/진행 로직 보유
  - `UCMDialoagueNode` / `UCMActionNode` : 대화 노드 & 액션 노드 트리 구조
  - `UCMLocalEventManager` : GameInstanceSubsystem, 대화용 델리게이트 허브
  - `UCMGameInstance` : GameInstance, 로컬 이벤트 매니저/세션 등 상위 관리
  - `UCMNpcDialogueWidget` : 대화 전체 UI, 텍스트/Next 버튼/선택지 컨테이너
  - `UCMNpcDialogueChoiceElement` : 개별 선택지 버튼 위젯
  - `UUIManagerComponent` : PlayerController에 부착, UI 스택 관리 및 뷰포트 표시

---

## 클래스 구조 (Mermaid 시각화)

### 상위 구조: GameInstance & Subsystem & NPC & UI

![](/assets/images/old/13e7c448-f690-492c-9faf-39fb9778cfc3-image.png)


### UI 구조: Dialogue Widget & Choice Element

![](/assets/images/old/1258ba38-ac63-437a-ba8b-91aa2e091f2d-image.png)


### 대화 노드 구조: 노드 트리 & 액션 노드

![](/assets/images/old/a5ece104-7d1c-471b-b621-f78e53542d1d-image.png)


---

## 이벤트 흐름 (상호작용 → 대화 → 선택지 → 종료)

다음 플로우 차트는 이벤트 흐름을 나타냅니다. 

![](/assets/images/old/7108c26f-f400-4b0e-86d8-a1af4246162a-image.png)



---

## 구현 상의 핵심 포인트

- GameInstanceSubsystem 활용
  - `UCMLocalEventManager` 를 `UGameInstanceSubsystem` 으로 두어, 맵 전환과 무관하게 대화 델리게이트를 공유 가능하게 설계
  - NPC, UI, 기타 시스템이 서로 직접 참조하지 않고 **이벤트 허브**를 통해 느슨하게 연결

- 델리게이트 기반 UI-로직 분리
  - NPC 쪽은 순수한 대화 트리/액션 처리에 집중
  - UI 쪽은 단지 델리게이트를 통해 텍스트와 선택지 정보를 받아 그리기만 함
  - 이로 인해 UI 변경(디자인 교체, 애니메이션 추가 등)이 NPC 로직에 영향을 주지 않음

- 액션 노드(선택지) 구조
  - 대화 트리는 `UCMDialoagueNode` 를 기본으로 하되, 선택지가 필요한 경우 파생 클래스 `UCMActionNode` 로 표현
  - 액션 노드는
    - `DialogueText` (선택지에 표시할 텍스트)
    - `ActionType` (ECMNpcComponentType) 을 가지며,
    - 선택 시 NPC가 어떤 컴포넌트의 어떤 액션을 수행해야 하는지 연결고리 역할을 수행

- EndDialogue 시 델리게이트 해제 철저
  - 대화 한 번 끝난 후에도 델리게이트가 남아있으면
    - 다음 대화에서 중복 호출, 크래시, 메모리 누수의 원인이 될 수 있음
  - `EndDialogue()` 에서 NPC ↔ LocalEventManager 간의 모든 바인딩을 명시적으로 해제

---

## 마치며
이번 NPC 대화 시스템 구현은 **데이터 구조(트리 기반 대화 노드)**, **델리게이트 기반 이벤트 흐름**, **UI/로직 분리**, **GameInstanceSubsystem 활용**이라는 네 가지 축을 중심으로 설계하고 구현하였습니다. 그 과정에서 UMG 바인딩, 델리게이트 시그니처, 포인터 관리 등 언리얼 특유의 함정들을 실제로 밟아 보며 정리할 수 있었고, 이를 통해 프로젝트 전반에서 재사용 가능한 패턴을 쌓을 수 있었다고 생각합니다.

앞으로는 이 구조 위에 퀘스트 시스템 연동, 세이브/로드 시 대화 상태 복원, 로컬라이제이션(다국어 지원) 등을 확장해 나가면서 NPC와의 상호작용 경험을 더욱 풍부하게 만들어 볼 계획입니다.

