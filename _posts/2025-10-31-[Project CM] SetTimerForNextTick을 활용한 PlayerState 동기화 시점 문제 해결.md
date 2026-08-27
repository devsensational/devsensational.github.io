---
title: "[Project CM] SetTimerForNextTick을 활용한 PlayerState 동기화 시점 문제 해결"
description: "오늘은 로비에서 PlayerState의 닉네임을 서버에서 클라이언트로 안정적으로 동기화하는 과정에서 발생한 문제를 분석하고 해결한 과정을 정리했습니다."
date: 2025-10-31T05:56:42.534Z
tags: ["project cm","ue5","troubleshooting"]
image:
  path: /assets/images/old/c35883c4-fd0f-4213-a6ef-5f5cfab54cc9-image.png
categories: [Project, Project CM + Project Arc]
---
오늘은 **로비에서 PlayerState의 닉네임을 서버에서 클라이언트로 안정적으로 동기화하는 과정**에서 발생한 문제를 분석하고 해결한 과정을 정리했습니다.
Lobby 흐름 중 `PlayerState`가 자신의 닉네임(`PendingNickname`)을 서버에서 설정하고 이를 클라이언트로 복제하는 구조입니다.
목표는 플레이어가 어떤 시점이든 접속 했을 때, 기존 접속 유저와 추가 접속 유저의 정보가 리스트에 정상적으로 등록되는 것입니다.

---

## UE5에서 PlayerState의 Replicated 변수 동기화 시점 연구

언리얼 엔진(UE5)에서 **`APlayerState`**는 플레이어 간에 공유되어야 하는 정보(예: 닉네임, 점수, 팀 정보 등)를 관리하는 클래스입니다. 특히 멀티플레이 환경에서는 이 클래스의 **Replicated 변수**들이 클라이언트와 서버 간에 자동으로 동기화되는데, 여기서 중요한 점이 하나 있습니다.

> **PlayerState의 Replicated 변수들이 언제 동기화되는지는 게임의 `BeginPlay()` 시점보다 빠르다고 보장할 수도, 느리다고 보장할 수도 없습니다.**

#### 왜 이런 일이 발생하나요?

UE의 네트워크 초기화 순서를 간단히 보면 다음과 같습니다.

1. 서버가 새로운 플레이어를 수용하면 `APlayerController`와 `APlayerState`를 생성합니다.
2. 클라이언트 측에서도 대응되는 객체들이 생성됩니다.
3. 서버는 이 객체들의 **Replication 데이터를 전송**하기 시작합니다.
4. `BeginPlay()`는 액터가 **월드에 스폰되고 초기화 절차를 마친 후** 호출됩니다.

문제는, **Replication 업데이트는 네트워크 패킷을 통해 비동기적으로 도착**한다는 점입니다.
따라서 클라이언트 입장에서는 `BeginPlay()`가 호출될 때 이미 모든 PlayerState 변수가 최신 상태로 동기화되어 있을 수도 있고, 반대로 아직 도착하지 않아 기본값(초기값)으로 남아 있을 수도 있습니다.

#### 예시: BeginPlay에서 접근 시 주의할 점

예를 들어, 다음 코드처럼 `BeginPlay()`에서 PlayerState의 데이터를 읽는 경우를 생각해 봅시다.

```cpp
void AMyCharacter::BeginPlay()
{
    Super::BeginPlay();

    if (APlayerState* PS = GetPlayerState())
    {
        UE_LOG(LogTemp, Warning, TEXT("Player Name: %s"), *PS->GetPlayerName());
    }
}
```

이때 `GetPlayerName()`이 올바른 값(예: "Player1")을 출력할 수도 있지만,
**아직 Replication이 끝나지 않았다면 빈 문자열("")이 나올 수도 있습니다.**

이것이 바로 “**동기화 시점을 보장할 수 없다**”는 의미입니다.

---

### 실제로 발생한 문제

* `OnRep_PendingNickname`이 호출되더라도 **GameState가 아직 초기화되지 않은 시점**이라면 로비 리스트 추가가 실패하거나 무시되는 현상이 있었습니다.
* 또한 `REPNOTIFY_Always` 설정으로 인해 **같은 PlayerState가 여러 번 리스트에 추가되는 중복 문제**도 발생했습니다.

---

### 원인 분석

1. **네트워크 복제와 월드 초기화의 비동기성**

   * `PlayerState`의 `OnRep`은 정상적으로 호출될 수 있지만, 그 시점에 `GameState`가 아직 준비되지 않았을 가능성이 있습니다.
   * 이로 인해 로비 리스트 접근 시 null 참조나 무시 현상이 발생

2. **복제 알림의 재진입 / 중복 문제**

   * `REPNOTIFY_Always`는 값이 동일하더라도 항상 `OnRep`을 트리거하기 때문에, **부수효과(리스트 추가)가 여러 번 실행될 수 있는 여지**가 있었음

---

### 해결 전략

#### 복제 보장 강화

* `DOREPLIFETIME_CONDITION_NOTIFY(..., REPNOTIFY_Always)`로 클라이언트 측에서 항상 `OnRep`을 받도록 유지
* 서버 `BeginPlay()`에서 `PendingNickname = GetName()` 식으로 **초기 값을 명확히 세팅**해 복제 타이밍을 안정화

#### 초기화 경합 해결 – SetTimerForNextTick 활용

* `GameState`가 아직 준비되지 않았다면 즉시 처리하지 않고 **`SetTimerForNextTick`** 등을 사용해 **다음 프레임으로 연기**
* 이를 통해 `GameState` 초기화가 완료된 이후에 로비 리스트 접근을 보장

#### 중복 방지 – `bAddedToLobby` 플래그

* PlayerState에 **bAddedToLobby** 추가
* 이미 추가된 상태라면 조기 종료하여, **`OnRep` 재호출이나 지연 처리 상황에서도 멱등성을 보장**

---

### 구현 요약

**서버 측**

* `BeginPlay()`에서 `PendingNickname`을 초기 설정
* `GetLifetimeReplicatedProps()`에 `DOREPLIFETIME_CONDITION_NOTIFY(..., REPNOTIFY_Always)` 등록

**클라이언트 측**

* `OnRep_PendingNickname()`에서 다음 순서로 처리했습니다

  1. 이미 추가된 경우(`bAddedToLobby == true`) 즉시 반환
  2. `GameState` 준비 여부 확인
  3. 준비되지 않았다면 `SetTimerForNextTick`으로 재시도 예약
  4. 준비 완료 시 로비 리스트에 안전하게 추가 후 `bAddedToLobby = true`

```cpp

void ACMPlayerStateLobby::OnRep_PendingNickname()
{
	if (PendingNickname.IsEmpty())
	{
		// 빈 문자열이면 FName이 NAME_None이 되므로 무시
		return;
	}

	HandlePendingNicknameChanged();
	UE_LOG(LogTemp, Log, TEXT("ACMPlayerStateLobby::OnRep_PendingNickname: %s"), *PendingNickname);
}

void ACMPlayerStateLobby::HandlePendingNicknameChanged()
{
    if (PendingNickname.IsEmpty())
    {
        return;
    }

    if (bAddedToLobby)
    {
        return;
    }
    bAddedToLobby = true;

    if (ACMGameStateLobby* GS = GetWorld()->GetGameState<ACMGameStateLobby>())
    {
    	GS->LobbyPlayerJoined.Broadcast(FName(*PendingNickname));
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("GameStateLobby not found."));
    	GetWorld()->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &ACMPlayerStateLobby::HandlePendingNicknameChanged));
		
    }
}
```

---

### 테스트 시나리오

* **단일 클라이언트 조인:** 즉시 혹은 1틱 지연 후 정상적으로 1회 추가됨을 확인했습니다.
* **다중 클라이언트 동시 조인:** 모든 클라이언트가 각각 1회만 리스트에 존재함을 확인했습니다.
* **느린 초기화 시뮬레이션:** `GameState` 지연 생성 시에도 다음 틱 재시도로 안정적으로 등록되었습니다.
* **재복제 / 재호출 상황:** `REPNOTIFY_Always`로 `OnRep`이 여러 번 호출되어도 `bAddedToLobby`로 인해 중복이 방지되었습니다.

### 테스트 결과
![](/assets/images/old/c35883c4-fd0f-4213-a6ef-5f5cfab54cc9-image.png)

본인을 제외한 다른 클라이언트들이 정상적으로 출력됩니다.

---

### 마치며

결국 `OnRep` 타이밍과 `GameState` 초기화 경합으로 인해 발생한 **불안정·중복 문제**는,
**SetTimerForNextTick**와 **가드 플래그(bAddedToLobby)**의 조합으로 간단하고 확실하게 해결되었습니다.

이 패턴은 **로비처럼 복제 직후 다른 서브시스템과 상호작용이 필요한 환경에서 재사용성이 높고**, 디버깅과 유지보수를 모두 단순화하는 매우 실용적인 접근 방식임을 확인했습니다.

다만, 초기화 시 발생하는 문제이므로 성능 상의 이슈가 크지는 않으나, 매 프레임마다 호출되는 것은 비효율적일 수 있으므로, 정해진 시간마다 호출하는 것을 고려할 수 있을 것 같습니다.

