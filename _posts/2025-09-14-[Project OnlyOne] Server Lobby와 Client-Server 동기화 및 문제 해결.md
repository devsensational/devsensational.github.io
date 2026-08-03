---
title: "[Project OnlyOne] Server Lobby와 Client-Server 동기화 및 문제 해결"
description: "플레이어가 서버에 접속하여 로비에서 다른 플레이어들과 함께 대기하고, Ready 상태를 관리할 수 있는 시스템을 구현했습니다."
date: 2025-09-14T15:27:49.035Z
tags: ["project onlyone","ue5","트러블슈팅"]
image:
  path: /assets/images/old/4c37f019-61b9-4667-bd3b-07c25fe050ac-image.webp
categories: [Project OnlyOne]
---
![](/assets/images/old/4c37f019-61b9-4667-bd3b-07c25fe050ac-image.webp)

플레이어가 서버에 접속하여 로비에서 다른 플레이어들과 함께 대기하고, Ready 상태를 관리할 수 있는 시스템을 만들었습니다. 특히 네트워크 동기화와 UI 업데이트에 중점을 두었습니다.

# 주요 기능
- **서버 접속 시스템**: IP 주소와 닉네임을 입력하여 서버에 접속
- **실시간 플레이어 목록**: 접속한 모든 플레이어를 실시간으로 표시
- **Ready 상태 관리**: 플레이어별 준비 상태를 토글하고 동기화
- **플레이어 입장/퇴장 알림**: 새 플레이어 입장 및 기존 플레이어 퇴장 시 실시간 UI 업데이트


## 시스템 아키텍처

### 핵심 클래스 구조

```
POMainMenuPlayerController (메인 메뉴)
    ↓ (서버 접속)
POServerLobbyPlayerController (로비 컨트롤러)
    ↔ POLobbyPlayerState (플레이어 상태)
    ↔ POServerLobbyWidget (로비 UI)
    ↔ POLobbyGameState (게임 상태)
```

### 실행 Sequence
![](/assets/images/old/d4649dc3-e8a2-4d11-bc5a-1deaa8c3bd38-image.png)

[해당 링크](https://mermaid.live/edit#pako:eNqdV21P21YU_itX_pRIISIQCLG0TuNlXSZeoqZs0hSpcuNLsObYmeNQKEKia1pRCCoIVqANCNSswMS0lEZVOlX7Qfj6P-xcXzuxEztsBSFyr89zzvFzznnuzSqXU0XM8VwJ_1LGSg5PSkJeEwpZBcFPUdB0KScVBUVHaVlYwRoSSsjcrxqnG-S4SV41e-2-VyXlR0nMY53apufoOoO1Jayx3V7EjCApM1gppycYor22Ik6oiq6psoy1XuRdoYBTSkkXIHGGde_02k8peUmxLOcVDQuyvdFrOK0-fLji5MOyZ1u3psTMMgzpwmR0QQ8K5KbLFSyIr_kUNTXOasanCl2QrRrZrJvPalmFGc-qOkYquLGLFgErHsWiiFRqxnUFkdNd8nzbwp3sImPr4uZDhSGZ_cCdO50q8lZFEeDMzc_IfNI03v3JjDs2XYA5ha7Gy7quKhOylPsZi6EwMg9b5GPtFmgqDcmWsKZAHRHZOCTnuz6ITsc4wRhtoc7HSUEXOjG7eek4iNg9wKOhHn7q65RhNz8dHGTh7jUeZbCexoooKfm0pi5IMg4ZWy-MSp2cVCLwWuTtZ_K86mXB7aDHn5PE6W_Ghyb8Wycnv_sk4abiviYsYXn-3jQiT49J5T0KfT0LPr9qJxK-xcF3koidNVRswOouSODdlQ_Q4Q0qjBWdxQ61UwjmnuEizozxaDiKQE-M6wuIVTGPDpHReIkgYXOzRd5UzV8_eUrA4K74dtGYC5gKBMpkvDxCoekHrmEKd6Hb0fvOt02kLzbD-0x4PwAEG8ewQ81DwfzYxhG3NvAoHnVPfHPjptUwj_Y9zNhAd7xUaVrNCXL3a0F0ct00n1wFAjOL6iNX_K7x7QI4Ofqol4cP1343dFbQpSUMGZZ0rZzzjecPtHWJ1vyadgw0zz45bhn7l4FQ-n7Gdgu6-ua6CkAPCoXmFEYX1RLLHhl778N-3qiqfiOK99UfJPyoqGq6NTNQFuOySQ52aKXM3RrIbFCRM0yZR6KeM7U9850qw0DQsh88M7YbTsY9lc-4W7O301CIivfxZytIiw7XwQ7MTjjQRQwSQOR8nRw0kPmmglKKpEuCLD3GU8tSSadKZxFV8u0OjysKnYWDgMr6t5pacEvdHPwFevBq4t22xjrObg_NWhLU2YFY8TqSiO7BOd9_Fu0yjToHBCMOtX3Adh1qxnSrVaVzulcjf-_QU3mz9f8ye5AqFGVcAEWFiVAVOqlbdfPVCxRisYPLNS6UsOMpgialUhGq42zYKQaCZ8oy3C-Ekt7pfSxaT91U_SeaEqBUf1wYe6fIt9-6G_kLUgrmyD9wAGcgA77qiEjjHxi8QFCPQETHNVUQaaoh9sR7-eijmOzywkD9sf7qN-9zek0xam7VX1orhpiGac7k6MuPq8tUuLxqtHllnP2FyMf9m8Y6czSfAjzD8vaxRGHk6YYXytQPkaOK8bba_3Y6FkXAOTlr-kohGymYAYjALkbkZIe8vgz3VZwgsWLdEgilmmMd5nbD2nm5Tnljrw6X05r5usqcyKpa9EvfON8wturM5guaiXl0O2R0hLs99u-rQDeeLvNvEN-a9DYEiLJfZ7Bp9PPh6QwuwuU1SeR4OPtxhCtgrSDQJbdKnWY5fRE6Osvx8FHECwLoQpbLKmsAg-9DP6lqwUFqajm_yPELglyCVbkoQq3sL7TtXQ1ypdNeVnSOjw2OxCwvHL_KLXP8QDyZjI6NxePDo7HEcDIxDE9XYDsWj0UHh0aTg_B8cGQoMRpfi3CPrchDUdgcg994IhkfGU7GEmv_AnEDZ5c)를 클릭하시면 더 자세히 보실 수 있습니다.

## 주요 도전과제와 해결방법

### 네트워크 타이밍 이슈

초기에는 클라이언트가 접속 시 PlayerState의 BeginPlay() 단계에서 기존에 로비에서 존재하던 플레이어들의 PlayerState를 가져와 Lobby 정보를 초기화 하려고 했습니다. 그러나, 서버로부터 동기화 되는 시간보다 더 빠르게 PlayerState에 접근하여 UI 초기화에 실패했습니다.

간단한 해결방법으로 타이머를 사용한 지연 초기화를 선택했습니다.

```cpp
if (GetNetMode() == NM_Client)
{
    FTimerHandle TimerHandle;
    GetWorld()->GetTimerManager().SetTimer(TimerHandle, 
        [this]() { InitializeExistingPlayers(); }, 
        1.0f, false);
}
```
하지만, 이 방법에는 네트워크의 지연이 더 심할 경우 보장되지 않는 위험이 여전히 존재합니다. 이후에는 PlayerState의 동기화 완료 플래그를 받아 해결할 예정입니다.

### 플레이어 퇴장 처리

초기에는 PlayerState의 BeginDestroy에서  플레이어의 퇴장 처리를 호출하려고 했습니다. 하지만, BeginDestroy 단계는, 플레이어가 서버에서 퇴장하자마자 실행되는 것이 아닌, GC가 실행될 때  호출되기 때문에 원하는 동작이 이루어지지 않았습니다.

이를 해결하기 위해 GameMode에서 Logout이 호출될 때, Multicast RPC를 호출하여 해당 UI가 로비에서 제거되도록 구현했습니다.
```cpp
void APOLobbyGameMode::Logout(AController* Exiting)
{
	if (APOLobbyPlayerState* PS = Exiting ? Exiting->GetPlayerState<APOLobbyPlayerState>() : nullptr)
	{
		PS->MulticastPlayerLeftLobby(PS->GetBaseNickname());
	}
	
	Super::Logout(Exiting);
}

void APOLobbyPlayerState::MulticastPlayerLeftLobby_Implementation(const FString& InName)
{
	FJoinServerData PlayerData;
	PlayerData.Name = BaseNickname;
	PlayerData.DisplayNickname = DisplayNickname;
	if (APOServerLobbyPlayerController* PC = Cast<APOServerLobbyPlayerController>(UGameplayStatics::GetPlayerController(this, 0)))
	{
		UE_LOG(POLog, Warning, TEXT("Broadcasting OnPlayerLeaveLobby for %s"), *BaseNickname);
		PC->OnPlayerLeaveLobby.Broadcast(PlayerData);
	}
}
```

# 마치며
아직까지 개선의 여지가 많은 소스코드입니다. 특히 네트워크 타이밍 이슈를 해결하기 위한 방법으로 지연을 선택한게 개인적으로 많이 아쉽습니다. 이후에 시간이 된다면 플래그를 활용한 비동기적 방법으로 개선하고자 합니다.