---
title: "[Project CM] PlayerState 추가/제거 함수 문제 발견 및 해결 방안 "
description: "로비에 접속 중인 플레이어 목록을 GameState에서 관리하기 위해 AddPlayerState와 RemovePlayerState를 오버라이드했지만, 실제로 호출되지 않았던 문제를 분석하고 해결했습니다."
date: 2025-10-30T09:04:51.778Z
tags: ["project cm","ue5","troubleshooting"]
image:
  path: /assets/images/old/7e09ef98-acf9-4b3b-a753-49c38cb7c318-image.png
categories: [Project, Project CM + Project Arc]
---
오늘은 로비에 접속 중인 플레이어 목록을 GameState에서 관리하기 위해 AddPlayerState와 RemovePlayerState를 오버라이드했지만, 실제로 호출되지 않았던 문제를 분석하고,
이를 GameMode의 PostLogin / Logout으로 대체하여 안정적으로 처리한 과정을 정리했습니다.

로비 시스템에서는 새로운 플레이어가 접속할 때마다 AddPlayerToLobby()를 호출해 목록에 추가하고, 퇴장 시 RemovePlayerFromLobby()로 제거하려는 구조였습니다. 하지만 예상과 달리 Add/Remove가 전혀 호출되지 않아 디버깅이 필요했습니다.

---
## 문제 상황

* 로비에서 플레이어가 입장하거나 퇴장해도
  `ACMGameStateLobby::AddPlayerState` / `RemovePlayerState`가 전혀 호출되지 않음.
* 로그 상에서 `GameMode`에서 `GetGameState<ACMGameStateLobby>()`가 실패하는 경우가 있었고,
  “GameState is not ACMGameStateLobby” 경고가 출력됨.
* 결과적으로 로비 플레이어 목록(`TArray<LobbyPlayers>`)이 갱신되지 않아 UI에 접속자 표시가 되지 않음.

---

## 원인 분석
### AddPlayerState / RemovePlayerState의 실제 호출 시점과 동작 원리

#### 1. Unreal Engine 내부 호출 흐름

`AGameStateBase`는 “게임의 전역 상태”를 관리하는 클래스이며,
`PlayerArray`를 통해 현재 세션(또는 레벨)에 접속해 있는 모든 `APlayerState`를 보관합니다.

이때 `AddPlayerState` / `RemovePlayerState`는 엔진이 아래의 시점에서 자동 호출합니다:

| 호출 함수                                      | 호출 타이밍                                                                                               | 호출 주체                              |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `AddPlayerState(APlayerState* PlayerState)`    | **서버에서 새로운 플레이어가 GameMode에 의해 성공적으로 로그인되어, GameState의 PlayerArray에 추가될 때** | `AGameModeBase::PostLogin()` 내부 흐름 |
| `RemovePlayerState(APlayerState* PlayerState)` | **플레이어가 세션에서 떠나거나(PlayerController가 Logout되거나 Destroy될 때)**                            | `AGameModeBase::Logout()` 내부 흐름    |

즉, **이 두 함수는 엔진이 자동으로 GameState의 PlayerArray를 갱신할 때** 불립니다.
개발자가 수동으로 호출할 일이 거의 없고, 호출되려면 반드시 아래 조건들이 모두 맞아야 합니다.

---

#### 2. 호출 조건

#### (1) 현재 활성 GameState 인스턴스가 올바른 타입일 것

* 맵의 `WorldSettings → GameMode Override → GameStateClass`가 `ACMGameStateLobby` 또는 이를 상속한 BP여야 함.
* 만약 다른 GameState가 활성화되어 있다면 (`BP_LobbyGameStateTest`가 ACMGameStateLobby를 상속하지 않음 등),
  `AddPlayerState`를 아무리 오버라이드해도 **그 함수는 절대 호출되지 않습니다.**

#### (2) 서버 권한(Authority) 컨텍스트일 것

* `AddPlayerState` / `RemovePlayerState`는 **서버 전용 함수**입니다.
* 서버가 GameMode를 통해 `GameState->AddPlayerState()`를 호출하여 PlayerArray를 갱신합니다.
* 클라이언트는 이 과정을 직접 수행하지 않으며,
  단순히 PlayerArray의 복제를 통해 `OnRep_PlayerArray()`가 호출될 뿐입니다.
* 따라서 클라이언트 로그만 보면, “내 오버라이드가 안 불린 것처럼” 보입니다.

#### (3) 정상적인 로그인 흐름일 것 (Spectator / Pending Kill 등 예외 X)

* 엔진은 PlayerController가 GameMode에 의해 **정상 로그인 처리**(`HandleStartingNewPlayer`)를 거쳐야 `AddPlayerState` 호출을 트리거합니다.
* 스펙테이터, 플레이어 교체(Reconnect), 트래블 중 임시 상태 등에서는
  `AddPlayerState`가 호출되지 않습니다.

---

#### 3. 왜 새 플레이어가 접속해도 AddPlayerState가 호출되지 않았는가


| 원인                      | 설명                                                                    |
| ------------------------- | ----------------------------------------------------------------------- |
| **GameStateClass 불일치** | 로비 맵의 GameMode가 ACMGameStateLobby가 아닌 다른 GameState를 사용 중. |
| **서버 전용 함수**        | Add/Remove는 서버 Authority에서만 호출됨. 클라 로그에서는 안 찍힘.      |
| **특수 로그인 흐름**      | Spectator나 Pending 상태의 컨트롤러는 AddPlayerState 호출 안 됨.        |

---

## 수정 사항

* `ACMGameModeLobby`에서 **PostLogin / Logout**을 활용해 직접 브로드캐스트하도록 수정했습니다.

```cpp
void ACMGameModeLobby::PostLogin(APlayerController* NewPlayer)
{
    Super::PostLogin(NewPlayer);

    if (ACMGameStateLobby* GS = GetGameState<ACMGameStateLobby>())
    {
        FString PlayerName = NewPlayer->PlayerState->GetPlayerName();
        GS->OnLobbyPlayerJoined.Broadcast(PlayerName);
    }
}

void ACMGameModeLobby::Logout(AController* Exiting)
{
    Super::Logout(Exiting);

    if (ACMGameStateLobby* GS = GetGameState<ACMGameStateLobby>())
    {
        FString PlayerName = Exiting->PlayerState->GetPlayerName();
        GS->OnLobbyPlayerLeft.Broadcast(PlayerName);
    }
}
```

* **입퇴장 시점 보장**이 되는 `GameMode`의 진입점에서 이벤트를 발행함으로써,
  로비 인원 수와 UI 갱신이 안정적으로 작동하도록 수정했습니다.

---

## 검증
![](/assets/images/old/7e09ef98-acf9-4b3b-a753-49c38cb7c318-image.png)

* 서버 로그 기준으로 입장/퇴장 시 `LobbyPlayerJoined` / `LobbyPlayerLeft` 이벤트가 확실히 호출됨.
* `GameState`에서 바인딩된 `AddPlayerToLobby()` / `RemovePlayerFromLobby()`가 정상 동작.
* `PostLogin`에서 `UE_LOG`로 현재 인원 수와 GameState 타입을 출력하여 올바른 호출 순서 확인.

---


##  결론

오늘의 핵심은, “**엔진의 호출 순서와 클래스 지정이 올바르지 않으면, 오버라이드는 절대 실행되지 않는다**”는 점입니다,

로비의 플레이어 목록을 `AddPlayerState`로 관리하려다 실패했지만, `PostLogin` / `Logout`으로 이벤트를 전환함으로써 해결할 수 있었습니다.
