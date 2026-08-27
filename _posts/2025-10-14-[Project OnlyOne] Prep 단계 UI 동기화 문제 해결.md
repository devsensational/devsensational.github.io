---
title: "[Project OnlyOne] Prep 단계 UI 동기화 문제 해결"
description: "준비 시간 때, Host에서는 UI가 정상적으로 출력되는데, Client에서는 UI가 출력되지 않는 문제가 발생했습니다."
date: 2025-10-14T11:54:37.488Z
tags: ["project onlyone","ue5","troubleshooting"]
image:
  path: /assets/images/old/91597b7d-fce9-4091-a884-463f6e8d9eaa-image.png
categories: [Project, Project OnlyOne]
---
![](/assets/images/old/91597b7d-fce9-4091-a884-463f6e8d9eaa-image.png)
![](/assets/images/old/77b7803a-d052-4893-a1d0-fc2d9c0ced48-image.png)

준비 시간 때, Host에서는 UI가 정상적으로 출력되는데, Client에서는 UI가 출력되지 않는 문제가 발생했습니다.

이전에는 EPOStagePhase가 변경되었을 때 Delegate가 호출되어 UI가 On/Off 되도록 구현했었습니다. None -> Prep -> Main 단계로 이어지기 때문에, Host에서는 Prep 단계로 변경될 때, PlayerController가 생성되어 있어 정상적으로 출력되었습니다. 하지만 Client는 PlayerController가 생성되기 전에 Prep단계로 변경되어 UI가 초기화될 수 없었습니다.

따라서, 해당 UI가 시작 직후에 반드시 생성되야 하는 UI 이므로 PlayerController가 준비되면 바로 On 하도록 수정했습니다. 남은 시간은 매 초마다 서버로부터 Replicated 되도록 구현되어 있으므로, 따로 수정하지 않아도 시간은 정상적으로 동기화 되었습니다.
```cpp
void APOPlayerController::BeginPlay()
{
	Super::BeginPlay();

	...
    
	// 로컬 컨트롤러에서만 HUD 위젯을 생성
	if (IsLocalController())
	{
    	...
		ShowPrevTimerWidget();
	}
    ...
 }
 
 
void APOPlayerController::OnChangeGamePhase(EPOStagePhase NewPhase)
{
	if (NewPhase != EPOStagePhase::Prep)
	{
		HidePrevTimerWidget();
	}
}
 ```
 
 이후 호스트와 클라이언트 모두 정상적으로 UI가 출력되었습니다.