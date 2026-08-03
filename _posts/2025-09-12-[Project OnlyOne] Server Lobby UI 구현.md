---
title: "[Project OnlyOne] Server Lobby UI 구현"
description: "Unreal Engine 5 멀티플레이어 게임의 서버 로비 시스템에서 플레이어 관리 기능을 구현했습니다. 플레이어의 입장, 퇴장, 준비 상태 관리를 동적으로 처리하는 UI 입니다."
date: 2025-09-12T11:45:49.189Z
tags: ["Project OnlyOne","UE5"]
categories: [Project OnlyOne]
---
![](/assets/images/old/550c39c5-2fd1-4454-826d-c2c3fe9e3961-image.webp)

Unreal Engine 5 멀티플레이어 게임의 서버 로비 시스템에서 플레이어 관리 기능을 구현했습니다. 플레이어의 입장, 퇴장, 준비 상태 관리를 동적으로 처리하는 UI 입니다.

# 플레이어 슬롯 동적 생성 및 관리
플레이어의 인원 수 만큼, 플레이어의 정보를 나타내는 UI가 필요합니다. 서버 로비에 플레이어가 입장할 때마다 동적으로 플레이어 슬롯 UI를 생성하고 관리하는 시스템을 구현했습니다.

## 1. 플레이어 입장 처리

```cpp
void UPOServerLobbyWidget::OnJoinPlayer(FJoinServerData& InNewPlayer)
{
	if (!PlayerSlotClass)
	{
		UE_LOG(POLog, Warning, TEXT("PlayerSlotClass is not set!"));
		return;
	}

	FString PlayerKey = InNewPlayer.Name;

	if (PlayerSlots.Contains(PlayerKey))
	{
		UE_LOG(POLog, Warning, TEXT("Player slot already exists for key: %s"), *PlayerKey);
		return;
	}

	if (UPOServerLobbyPlayerElementWidget* NewPlayerSlot = CreateWidget<UPOServerLobbyPlayerElementWidget>(this, PlayerSlotClass))
	{
		PlayerSlots.Add(PlayerKey, NewPlayerSlot);
		
		NewPlayerSlot->AddToViewport();
		NewPlayerSlot->SetPlayerName(InNewPlayer.Name);
		PlayerListScrollBox->AddChild(NewPlayerSlot);
		
		UE_LOG(POLog, Log, TEXT("Created and stored player slot for player: %s"), *PlayerKey);
	}
	else
	{
		UE_LOG(POLog, Error, TEXT("Failed to create player slot widget"));
	}
}
```

### 핵심 포인트

- TMap<FString, TObjectPtr<UPOServerLobbyPlayerElementWidget>> PlayerSlots를 사용한 플레이어 슬롯 관리
- 플레이어 이름을 키로 사용하여 중복 방지
- CreateWidget을 통한 동적 위젯 생성
- ScrollBox에 자동으로 추가하여 UI 업데이트
  
## 2. 플레이어 퇴장 처리
플레이어가 로비를 떠날 때 해당 플레이어의 UI 슬롯을 안전하게 제거하는 기능을 구현했습니다.
```cpp
void UPOServerLobbyWidget::OnExitPlayer(FJoinServerData& InExitPlayer)
{
	if (PlayerSlots.Contains(InExitPlayer.Name))
	{
		if (UPOServerLobbyPlayerElementWidget* PlayerSlot = PlayerSlots[InExitPlayer.Name])
		{
			PlayerSlot->RemoveFromParent();
			PlayerSlots.Remove(InExitPlayer.Name);
			UE_LOG(POLog, Log, TEXT("Removed player slot for player: %s"), *InExitPlayer.Name);
		}
	}
	else
	{
		UE_LOG(POLog, Warning, TEXT("No player slot found for player: %s"), *InExitPlayer.Name);
	}
}
```
  
### 핵심 포인트
- 메모리 누수 방지를 위한 적절한 위젯 제거
- `RemoveFromParent()`를 통한 UI 계층에서의 안전한 제거
- 맵에서도 동시에 제거하여 데이터 일관성 유지

## 3. 플레이어 준비 상태 관리
각 플레이어의 준비 상태를 실시간으로 업데이트하는 시스템을 구현했습니다.
```cpp
void UPOServerLobbyWidget::OnReadyPlayer(const FJoinServerData& InReadyPlayer, bool bIsReady)
{
	if (PlayerSlots.Contains(InReadyPlayer.Name))
	{
		if (UPOServerLobbyPlayerElementWidget* PlayerSlot = PlayerSlots[InReadyPlayer.Name])
		{
			PlayerSlot->SetPlayerReadyState(bIsReady);
			UE_LOG(POLog, Log, TEXT("Set ready state for player: %s to %s"), *InReadyPlayer.Name, bIsReady ? TEXT("Ready") : TEXT("Not Ready"));
		}
	}
	else
	{
		UE_LOG(POLog, Warning, TEXT("No player slot found for player: %s"), *InReadyPlayer.Name);
	}
}
```

## 4. 테스트 기능 구현
개발 및 디버깅을 위한 테스트 버튼 기능을 추가했습니다.

```cpp
void UPOServerLobbyWidget::TestJoinButtonClicked()
{
    FJoinServerData TestPlayer;
    TestPlayer.Name = TEXT("Test player" + FString::FromInt(PlayerSlots.Num() + 1));
    TestPlayer.IPAddress = TEXT("123456");
    OnJoinPlayer(TestPlayer);
}

void UPOServerLobbyWidget::TestExitButtonClicked()
{
    FJoinServerData TestPlayer;
    TestPlayer.Name = TEXT("Test player" + FString::FromInt(PlayerSlots.Num()));
    OnExitPlayer(TestPlayer);
}
```

## 테스트 결과
![](/assets/images/old/ee54d131-72b4-46bf-b24d-6da5a33af588-image.webp)
  
## 마무리
오늘 구현한 서버 로비 시스템은 멀티플레이어 게임의 핵심적인 기능 중 하나입니다. 동적 UI 생성, 안전한 메모리 관리, 이벤트 기반 아키텍처 등을 통해 확장 가능하고 유지보수하기 쉬운 시스템을 구축할 수 있었습니다.

특히 TMap을 활용한 플레이어 슬롯 관리와 CreateWidget을 통한 동적 위젯 생성 패턴은 다른 UI 시스템에서도 응용할 수 있는 유용한 기법이라고 생각합니다.

