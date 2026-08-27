---
title: "[Project CM] 로비에 접속한 플레이어에게 파티 초대 요청하는 기능 구현"
description: "오늘은 로비 초대(Party Invite) 시스템을 직접 구현했습니다. 로비 내에서 플레이어가 다른 플레이어를 초대하고, 상대방이 초대 팝업을 통해 수락 또는 거절할 수 있도록 하는 기능입니다."
date: 2025-11-02T07:34:08.917Z
tags: ["project cm","ue5"]
image:
  path: /assets/images/old/db753cec-5904-44cf-826d-f934c4447c6a-image.png
categories: [Project, Project CM + Project Arc]
---
오늘은 **로비 초대(Party Invite) 시스템**을 직접 구현했습니다.
로비 내에서 플레이어가 다른 플레이어를 초대하고, 상대방이 초대 팝업을 통해 수락 또는 거절할 수 있도록 하는 기능입니다.

---

### 1. 시스템 구조 개요

#### GameMode: `ACMGameModeLobby`

* **역할**: 서버에서 로그인 직후(`PostLogin`) 플레이어 컨트롤러를 `GameState`에 등록합니다.
* **구현 내용**:
  `ACMGameStateLobby::AddLookingPlayer`를 호출하여 `닉네임 → PlayerController` 매핑을 구성했습니다.
  이렇게 등록된 정보는 이후 초대 대상 탐색 시 사용됩니다.

#### GameState: `ACMGameStateLobby`

* **역할**: 로비 접속자 목록 관리 및 초대 라우팅(서버 → 클라이언트).
* **구현 내용**:
  `PerformInvitePlayer(FromPlayer, ToPlayer)`를 통해 초대 요청을 처리합니다.
  `CurrentLookingPlayers`에서 `ToPlayer`를 찾아 대상 컨트롤러를 얻고,
  `ClientNotifyPartyInviteReceived(FromPlayer)`를 호출하여 초대 알림을 전달합니다.

#### PlayerController: `ACMPlayerControllerLobby`

* **역할**: 초대 요청 송신(클라이언트 → 서버 RPC), 초대 수신 시 UI 표시.
* **구현 내용**:

  * 초대 버튼 클릭 시 `InvitePlayer(ToPlayer)` 호출 → `HandlePartyRequestInvite(ToPlayer)` 서버 RPC 실행.
  * 서버에서는 본인의 `PendingNickname`을 `FromPlayer`로 가져와 `GameState`에 초대 요청을 전달합니다.
  * 초대를 받은 클라이언트는 `HandlePartyInviteReceived(FromPlayer)`를 통해 초대 팝업을 표시합니다.

#### PlayerState: `ACMPlayerStateLobby`

* **역할**: `PendingNickname`을 관리하여 GameState의 매핑 키로 활용했습니다.

#### Widget: `UCMWidgetInviteParty`

* **역할**: 초대 팝업 UI (수락/거절 버튼 포함).
* **구현 내용**:

  * `UCMWidgetTwoButtonWindow`를 상속한 팝업 형태로 제작했습니다.
  * 초대 수신 시 위젯이 생성되고 `FromPlayer` 정보를 전달받아 초대한 사람의 닉네임을 표시합니다.
  * 현재 수락(`AcceptInvite`) / 거절(`DeclineInvite`)은 내부 로직을 연결하기 전 단계로,
    추후 실제 파티 합류 RPC와 연동할 예정입니다.

---

### 2. 동작 흐름

![](/assets/images/old/db753cec-5904-44cf-826d-f934c4447c6a-image.png)

1. **로그인 시 등록 (서버)**

   * `GameModeLobby::PostLogin` → `GameStateLobby::AddLookingPlayer`
   * `PlayerState`의 `PendingNickname`을 키로 하여 `TMap<FName, ACMPlayerControllerLobby*>`에 등록.

2. **초대 요청 (클라이언트 → 서버)**

   * `InvitePlayer(ToPlayer)` → `HandlePartyRequestInvite(ToPlayer)` 서버 RPC
   * 서버에서 `FromPlayer`를 본인 닉네임으로 가져와 `PerformInvitePlayer(FromPlayer, ToPlayer)` 호출.

3. **초대 라우팅 (서버)**

   * `GameState`가 `CurrentLookingPlayers`에서 대상(`ToPlayer`) 컨트롤러를 찾고
     `ClientNotifyPartyInviteReceived(FromPlayer)`로 클라이언트에 알림.

4. **초대 수신 및 UI 표시 (클라이언트)**

   * `HandlePartyInviteReceived(FromPlayer)` 실행 → 위젯 생성 (`CreateWidget`)
   * `FromPlayer` 정보를 위젯에 전달해 “○○님이 초대했습니다” 형태로 표시.
   * 팝업이 이미 존재한다면 가시성을 `Visible`로 전환.

5. **UI 동작 (수락/거절 예정)**

   * `AcceptInvite` / `DeclineInvite` 함수는 현재 비어 있으며,
     추후 서버 RPC와 연결하여 파티 참가 여부를 처리할 예정입니다.
---

### 3. 실제 적용
![](/assets/images/old/6eaa0948-4c8e-418b-92d7-0135cd339bb4-image.webp)



---

### 마치며

이번 작업을 통해 **로비 초대 시스템의 전반적인 흐름**을 직접 구현하며, 서버와 클라이언트 간의 RPC 구조를 명확히 잡을 수 있었습니다.

다음 단계는 초대 수락/거절 로직을 실제 파티 참여 기능과 연결하여
완전한 **로비 파티 시스템**으로 발전시키는 것입니다.
