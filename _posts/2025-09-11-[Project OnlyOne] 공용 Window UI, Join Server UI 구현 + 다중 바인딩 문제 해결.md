---
title: "[Project OnlyOne] 공용 Window UI, Join Server UI 구현 + 다중 바인딩 문제 해결"
description: "윈도우 형 UI를 위한 공용 Window UI WBP, 서버에 접속할 때 필요한 정보를 적을 수 있는 UI를 구현했습니다."
date: 2025-09-11T10:29:04.623Z
tags: ["Project OnlyOne","UE5","트러블슈팅"]
image:
  path: /assets/images/old/3b7c77d4-66fc-46a2-8122-56148b7cf5d9-image.webp
categories: [Project OnlyOne]
---
![](/assets/images/old/3b7c77d4-66fc-46a2-8122-56148b7cf5d9-image.webp)

윈도우 형 UI를 위한 공용 Window UI WBP, 서버에 접속할 때 필요한 정보를 적을 수 있는 UI를 구현했습니다.

# 재사용을 위한 Window UI Class
Join Server UI뿐만 아니라 Setting, 알림창 등 다양한 UI에서 같은 윈도우 형식이 반복적으로 쓰일 가능성이 크기 때문에, 이를 하나의 **재사용 가능한 Window WBP**로 만들어 두는 것이 효율적이라고 판단했습니다.

#### Window WBP 기본 기능

* **Border**: UI의 크기를 명확히 구분할 수 있도록 테두리를 설정
* **닫기 버튼**: 윈도우 자체를 숨길 수 있도록 버튼 추가

#### 발생한 문제

Window WBP를 다른 WBP에 추가해 사용할 때, **닫기 버튼이 Window UI만 숨기고 실제 콘텐츠는 그대로 남아 있는 문제**가 발생했습니다. 단순히 Visibility를 변경하는 것만으로는 원하는 동작을 얻을 수 없었습니다.

#### 해결 방법

이를 해결하기 위해 **Delegate 방식**을 도입했습니다.

1. Window WBP 내부에 **Delegate를 선언**
2. 닫기 버튼 클릭 시 해당 Delegate를 **Broadcast**
3. Window WBP를 포함하는 콘텐츠 클래스에서는

   * `meta=(BindWidget)`을 통해 Window WBP를 레퍼런싱
   * Delegate에 **AddDynamic**을 통해 처리 로직 바인딩
   
4. 이렇게 하면 콘텐츠 쪽에서 닫기 동작을 원하는 방식대로 제어할 수 있음

```cpp
//POBaseWindow.h
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCloseWindow);

UCLASS()
class ONLYONE_API UPOBaseWindow : public UPOBaseWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void BeginDestroy() override;

	UPROPERTY(BlueprintAssignable)
	FOnCloseWindow OnCloseWindow;
	
protected:
	UPROPERTY(meta = (BindWidget))
	UButton* ExitButton;

	UFUNCTION()
	void OnExitButtonClicked();
};
```

```cpp
//POBaseWindow.cpp
void UPOBaseWindow::NativeConstruct()
{
	Super::NativeConstruct();
	
	if (ExitButton)
	{
		ExitButton->OnClicked.AddDynamic(this, &UPOBaseWindow::OnExitButtonClicked);
	}
}

void UPOBaseWindow::BeginDestroy()
{
	OnCloseWindow.Clear();
	
	Super::BeginDestroy();
}

void UPOBaseWindow::OnExitButtonClicked()
{
	OnCloseWindow.Broadcast();
}
```
```cpp
//POJoinServerWidget.cpp
void UPOJoinServerWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (WindowUI && !WindowUI->OnCloseWindow.IsBound())
	{
		WindowUI->OnCloseWindow.AddDynamic(this, &UPOJoinServerWidget::OnCloseWindow);
	}
    ...
}
```
인스턴스가 삭제될 때에는 꼭 바인딩된 델리게이트를 정리합니다.

# Join Server UI 구현
![](/assets/images/old/9de71e69-9291-4b73-8ef8-ea439a3a1a75-image.png)

해당 UI를 구현할 때에는 구현된 윈도우 UI를 재사용하고, 컨텐츠를 추가합니다.

![](/assets/images/old/a65d07a5-51f5-456c-8c6b-318cbb687c3a-image.png)

테스트 결과 문자열이 잘 전달됩니다.

![](/assets/images/old/53e412d3-b9d4-4237-8cf2-c4c5766da8eb-image.webp)


# 다중 바인딩 문제 해결
현재 UI는 ```POMainMenuPlayerController```에서 관리되고 있습니다. 처음에는 Join Server 버튼을 누르면 ```ShowJoinServer()``` 함수가 호출되어 위젯에서 `AddToViewport()`를 호출하도록 구현했습니다.

그런데 `AddToViewport()`가 호출될 때 마다 해당 위젯의 Delegate 바인드가 포함된 `NativeConstruct()`가 계속 호출 되었고, 여러 번 바인딩 되는 문제가 발생했습니다.

따라서, 처음 UI를 생성할 때에만 `AddToViewport()`를 호출하고 그 외에는 `SetVisibility()`를 사용하여 노출 상태를 수정하도록 했습니다. 

```cpp
//POMainMenuPlayerController.h
void APOMainMenuPlayerController::ShowJoinServer()
{
	if (JoinServerWidgetClass)
	{
		if (!JoinServerWidget)
		{
			JoinServerWidget = CreateWidget<UPOJoinServerWidget>(this, JoinServerWidgetClass);
			JoinServerWidget->AddToViewport();
			SetInputMode(FInputModeUIOnly());
		}

		if (JoinServerWidget)
		{
			JoinServerWidget->SetVisibility(ESlateVisibility::Visible);
		}
	}
}
```

또한, 바인딩 될 때에도 IsBound()를 한번 체크하도록 수정했습니다.

이를 통해, 안정적인 UI 팝업을 구현할 수 있었습니다.
