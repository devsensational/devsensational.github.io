---
title: "[Project OnlyOne] Main UI 프로토타입 구현"
description: "게임의 메인 화면에서 사용될 UI의 프로토타입을 구현하였습니다. 버튼 애니메이션을 재사용하기 위해 커스텀 버튼 클래스를 구현해 사용했습니다."
date: 2025-09-10T10:57:45.148Z
tags: ["Project OnlyOne","UE5"]
thumbnail: /assets/images/old/0cc192a0-e281-4e2c-b4aa-816d0a307bea-image.webp
categories: [Project OnlyOne]
---
![](/assets/images/old/0cc192a0-e281-4e2c-b4aa-816d0a307bea-image.webp)

게임의 메인 화면에서 사용될 UI의 프로토타입을 구현하였습니다.

# 재사용을 위한 Button UI Class
처음에는 HUD에 버튼을 생성하고, MainMenu용 클래스에 UButton*을 bind로 지정하여 클릭 이벤트를 처리하려고 했습니다. 그러나 하나의 Widget에는 하나의 Animation만 지정되는 문제가 있었습니다. 

**즉, 버튼이 늘어날 때 마다 똑같은 애니메이션을 여러개 만들어야 하는 문제가 발생했습니다.**

따라서, 재사용 할 수 있는 버튼 클래스를 만들고, 이를 상속받은 WBP를 구현, 이 Widget들을 MainMenu WBP에 추가하도록 구현했습니다.
```cpp
// UPOCustomButton.h
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnFadeButtonClicked, class UPOCustomButton*, ClickedButton);

UCLASS()
class ONLYONE_API UPOCustomButton : public UUserWidget
{
	GENERATED_BODY()
public:
	UPOCustomButton(const FObjectInitializer& ObjectInitializer);

	UPROPERTY(BlueprintAssignable, Category = "Button Events")
	FOnFadeButtonClicked OnCustomButtonClicked;
    
	UFUNCTION(BlueprintCallable, Category = "Button")
	void SetButtonEnabled(bool bEnabled);

	UFUNCTION(BlueprintCallable, Category = "Button")
	void SetButtonText(const FText& InText);

protected:
	virtual void NativeConstruct() override;
    
	UPROPERTY(meta = (BindWidget))
	UButton* MainButton;

	UPROPERTY(meta = (BindWidget))
	UTextBlock* ButtonText;

	UFUNCTION()
	void OnButtonClicked();
    
private:
	bool bIsEnabled;
};
```

```cpp
// UPOMainMenuWidget.cpp
void UPOMainMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// 버튼 바인딩
	if (JoinServerButton)
	{
		JoinServerButton->SetButtonText(FText::FromString("Join Server"));
		JoinServerButton->OnCustomButtonClicked.AddDynamic(this, &UPOMainMenuWidget::OnJoinServerClicked);
	}
	
	if (SettingsButton)
	{
		SettingsButton->SetButtonText(FText::FromString("Setting"));
		SettingsButton->OnCustomButtonClicked.AddDynamic(this, &UPOMainMenuWidget::OnSettingsClicked);
	}
	
	if (QuitButton)
	{
		QuitButton->SetButtonText(FText::FromString("Quit"));
		QuitButton->OnCustomButtonClicked.AddDynamic(this, &UPOMainMenuWidget::OnQuitClicked);
	}
}

void UPOMainMenuWidget::OnJoinServerClicked(UPOCustomButton* ClickedButton)
{
	// TODO: 서버 접속 로직 구현
	UE_LOG(LogTemp, Warning, TEXT("Join Server Clicked"));
}

void UPOMainMenuWidget::OnSettingsClicked(UPOCustomButton* ClickedButton)
{
	// TODO: 설정 화면 열기 로직 구현
	UE_LOG(LogTemp, Warning, TEXT("Settings Clicked"));
}

void UPOMainMenuWidget::OnQuitClicked(UPOCustomButton* ClickedButton)
{
	// 게임 종료
	if (UWorld* World = GetWorld())
	{
		UKismetSystemLibrary::QuitGame(World, nullptr, EQuitPreference::Quit, false);
	}
}
```

```OnCustomButtonClicked``` Delegate에 필요한 함수를 바인딩하여 클릭할 때 그 함수가 호출되도록 구현했습니다. 애니메이션은 에디터의 기능들을 사용해 구현했습니다.
![](/assets/images/old/ab805bd5-5731-4b51-96e0-3bc15c738b19-image.png)

# 완성된 메인 메뉴

![](/assets/images/old/7a4e16e3-853e-4e5a-ba71-68776e800e0c-image.webp)
