---
title: "[Project Arc] NPC 시스템 설계"
description: "오늘은 ACMNpcBase를 중심으로, 다양한 NPC 기능(대화, 퀘스트, 상점 등)을 컴포넌트 기반으로 확장할 수 있는 구조를 설계하였습니다."
date: 2025-12-03T10:35:29.064Z
tags: ["project arc","ue5"]
image:
  path: /assets/images/old/938aac1a-a10e-416f-965c-be1f28178dbb-image.png
categories: [Project CM + Project Arc]
---
오늘은 `ACMNpcBase`를 중심으로, 다양한 NPC 기능(대화, 퀘스트, 상점 등)을 **컴포넌트 기반**으로 확장할 수 있는 구조를 설계하였습니다. 이 구조를 통해 이후 요구사항 변화에 유연하게 대응할 수 있도록 확장성과 유지보수성을 고려한 아키텍처를 목표로 하였습니다.

---

## 설계 목표

- 컴포넌트 기반 NPC 확장 구조 설계
  - 공통된 NPC 베이스 클래스: `ACMNpcBase`
  - 기능 단위의 컴포넌트: `UCMNpcComponentBase` 파생 클래스들
- 기능별 책임 분리
  - 대화(Dialogue), 퀘스트(Quest), 상점(Shop) 기능을 각각 독립된 컴포넌트로 관리
- 타입 기반 액션 처리
  - `ECMNpcComponentType` + `HandleActionByType()` 조합으로 컴포넌트 접근
- 향후 기능 추가에 대비한 확장성
  - 새로운 NPC 기능을 추가할 때 기존 코드 수정을 최소화

---

## 핵심 클래스 및 인터페이스 구조

- `ACMNpcBase : AActor, ICMNpcHandler`
  - NPC의 공통 베이스 액터
  - `ICMNpcHandler` 인터페이스를 구현하여 외부에서 통합된 방식으로 NPC에 요청 전달
- `ICMNpcHandler`
  - NPC가 공통으로 가져야 할 행동 인터페이스 정의
  - 예: `HandleActionByType(ECMNpcComponentType ComponentType)`
- `UCMNpcComponentBase`
  - NPC 기능용 베이스 컴포넌트 클래스
  - Dialogue / Quest / Shop 등 기능 컴포넌트의 부모 타입
- `ECMNpcComponentType`
  - NPC 컴포넌트 타입 식별용 enum
  - `Default`, `DialogueComponent`, `QuestComponent`, `ShopComponent` 등 정의

---

## 클래스 다이어그램

![](/assets/images/old/938aac1a-a10e-416f-965c-be1f28178dbb-image.png)

---

## ACMNpcBase의 역할 및 책임 정리

- NPC 공통 Actor 베이스
  - 카메라 컴포넌트: `NpcCameraComponent`
  - 캡슐 콜라이더: `CapsuleComponent`
  - 스켈레탈 메시: `MeshComponent`
- NPC 기능 컴포넌트 관리
  - `NpcComponents` 배열로 부착된 컴포넌트들을 보관
  - `RegisteredComponentMap<ECMNpcComponentType, UCMNpcComponentBase*>`로 타입-컴포넌트 매핑
- 컴포넌트 등록 로직
  - `RegisterComponent(ECMNpcComponentType ComponentType, UCMNpcComponentBase* NewComponent)`
    - 외부/컴포넌트에서 자기 자신을 등록하는 공용 인터페이스
  - `PerformRegisterComponent(...)`
    - 중복 등록 체크, 맵 갱신 등 실제 등록 로직 처리
- 상호작용 처리
  - `PerformInteract()`
    - 플레이어가 NPC와 상호작용할 때 호출되는 Entry Point
    - 적절한 `ECMNpcComponentType`를 결정 후 `HandleActionByType()` 호출 가능

---

## ICMNpcHandler 인터페이스 활용

- 공통 액션 처리 진입점 제공
  - `HandleActionByType(ECMNpcComponentType ComponentType)`
    - 컴포넌트 타입 기반으로 적절한 NPC 컴포넌트를 찾아 액션 실행
- 컴포넌트 등록 책임의 일원화
  - `RegisterComponent(ECMNpcComponentType ComponentType, UCMNpcComponentBase* NewComponent)`
    - NPC 베이스에서만 타입-컴포넌트 매핑을 관리하도록 강제
- 장점
  - 외부에서 NPC의 내부 구조(어떤 컴포넌트가 있는지)를 몰라도, enum 타입과 핸들러 메서드만으로 행동 요청 가능
  - 추후 새로운 컴포넌트 타입이 추가되어도, 인터페이스 시그니처는 유지되므로 기존 호출부 영향 최소화

---

## 컴포넌트 기반 확장성 (Dialogue / Quest / Shop)

- 컴포넌트 유형 정의
  - `ECMNpcComponentType::DialogueComponent`
  - `ECMNpcComponentType::QuestComponent`
  - `ECMNpcComponentType::ShopComponent`
- 각 기능의 책임 분리
  - Dialogue 컴포넌트
    - NPC 대사를 관리하고, 트리 기반 대화 흐름 제어
  - Quest 컴포넌트
    - 퀘스트 제공, 진행 상태 관리, 완료 조건 체크
  - Shop 컴포넌트
    - 상점 인벤토리, 구매/판매 로직 관리
- 확장성 포인트
  - 새로운 기능(예: `ECMNpcComponentType::TrainingComponent`, `CraftComponent` 등)을 추가할 때
    - enum에 타입만 추가
    - 해당 타입을 담당하는 `UCMNpcComponentBase` 파생 컴포넌트 생성
    - `RegisterComponent()`를 통해 `ACMNpcBase`에 등록
  - 기존 `HandleActionByType()` 호출 구조는 그대로 유지
- 유지보수성 향상 요소
  - 기능 단위로 클래스가 나뉘어 있어, 버그 수정 또는 기능 변경 시 해당 컴포넌트에만 집중 가능
  - 공통 인터페이스(`ICMNpcHandler`, `UCMNpcComponentBase`)를 통해 일관된 사용법 제공

---

## 8. HandleActionByType() 기반 액션 라우팅

- 목적
  - 외부 코드(플레이어 상호작용, 트리거, UI 등)에서 NPC에게 특정 기능을 요청할 때, 컴포넌트를 직접 참조하지 않고 타입 기반으로 접근
- 처리 흐름
  - 입력: `ECMNpcComponentType ComponentType`
  - `RegisteredComponentMap`에서 해당 타입의 컴포넌트 조회
  - 컴포넌트가 존재하면 `UCMNpcComponentBase::HandleAction()` (또는 유사 메서드) 호출
- 장점
  - NPC 내부 구조 변경(컴포넌트 교체, 리팩토링)에도 외부 인터페이스 유지
  - 다양한 상호작용(예: 대화 / 퀘스트 수락 / 상점 열기)을 **타입 하나로 추상화** 가능

---

## 트리형 Dialogue 설계와 HandleActionByType() 연계

- 트리형 Dialogue 구조 계획
  - 노드 기반 대화 구조
    - 각 노드는 대사 내용, 선택지, 다음 노드에 대한 참조를 가짐
  - 플레이어 선택에 따라 다른 노드로 분기하는 트리(또는 DAG) 형태
- Dialogue 컴포넌트 역할
  - 내부에 대화 트리 데이터 구조 보관
  - `StartDialogue()`, `ProceedToNextNode(ChoiceIndex)`, `EndDialogue()` 등의 메서드 제공
  - `HandleAction()`에서 초기 진입점(`StartDialogue()`) 호출
- HandleActionByType() 활용 시나리오
  - 플레이어가 NPC와 상호작용 → `ACMNpcBase::PerformInteract()` 호출
  - 현재 상황(퀘스트 단계, 게임 모드 등)에 따라 아래 중 하나를 선택
    - `HandleActionByType(ECMNpcComponentType::DialogueComponent)`
    - `HandleActionByType(ECMNpcComponentType::QuestComponent)`
    - `HandleActionByType(ECMNpcComponentType::ShopComponent)`
  - Dialogue 선택 시
    - 등록된 Dialogue 컴포넌트를 조회 → 대화 트리의 루트 노드에서 대화 시작
- 확장 시 이점
  - 트리 구조나 대화 데이터 포맷이 바뀌더라도 `HandleActionByType(DialogueComponent)` 호출부는 변경 없이 유지 가능
  - 대화 로직 복잡도가 커져도, NPC 베이스/외부 호출부와 분리되어 유지보수 부담 감소

---

## 마치며

이번 NPC 설계에서는 **Actor + Interface + Component + Enum**을 조합하여, NPC의 다양한 기능을 느슨하게 결합된 형태로 구성해 보았습니다. 특히 `HandleActionByType()`과 `ECMNpcComponentType`을 활용하여 컴포넌트에 접근하는 방식은, 이후 Dialogue, Quest, Shop 컴포넌트가 추가되더라도 외부 인터페이스를 거의 건드리지 않고 확장이 가능하다는 장점이 있었습니다.

앞으로는 실제 트리형 Dialogue 데이터를 설계하고, 이를 처리하는 Dialogue 컴포넌트를 구현하면서, 이번에 정의한 NPC 베이스 구조가 얼마나 유연하게 동작하는지 검증해 볼 예정입니다. 이를 통해 상호작용이 복잡해지는 RPG 스타일 게임에서도 유지보수성과 확장성을 동시에 확보하는 NPC 아키텍처를 완성하는 것을 목표로 삼겠습니다.

