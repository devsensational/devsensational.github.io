---
title: "[TPS프로젝트] (4) Object Pooling과 이벤트 매니저를 활용한 아이템 상호작용과 인벤토리 UI 구현"
description: "개발은 결국 비용과의 싸움입니다. 여기서 비용은 조금 포괄적인 개념입니다. 돈이 될 수도 있고, 시간(일정)이 될 수도 있고, 연산에 필요한 데이터를 메모리에서 가져오는 행위도 될 수 있습니다. "
date: 2024-06-10T07:55:59.915Z
tags: ["C#","Unity"]
thumbnail: /assets/images/old/0d07310e-f0a4-4684-9ec2-df06d5c8e58e-image.webp
categories: [TPSProject]
---
**개발은 결국 비용과의 싸움입니다.** 여기서 비용은 조금 포괄적인 개념입니다. 돈이 될 수도 있고, 시간(일정)이 될 수도 있고, 연산에 필요한 데이터를 메모리에서 가져오는 행위도 될 수 있습니다. 개발자는 제가 설명한 "비용"보다 더 많은 종류의 비용을 만족가능한 범위 내에서 사용해야 합니다. 최종적으로 사용자가 만족할 수 있도록 말입니다.

## Object Pooling
CPU는 정말로 빠릅니다. 우리가 생각하는 것보다 더 빠를 것입니다. 하지만 폰 노이만으로 부터 시작된 현대의 컴퓨터는 이어 달리기나 다름 없습니다. 아무리 빠른 달리기 선수라고 하더라도 이전 순서의 선수에게 바톤을 받지 못하면 출발할 수 없습니다. 여기서 이전 선수는 메모리, 바톤은 데이터라고 할 수 있겠습니다. CPU는 결국 달리기 위해서 메모리가 데이터를 가져다 줄 때 까지 기다릴 수 밖에 없습니다. 이 것이 사용자가 컴퓨터가 순간적으로 멈춘 것 처럼 보이는 프리징 현상을 보이는 이유 중 하나라고 설명할 수 있습니다.

**Object Pooling은 이전 주자가 전날에 미리 달리고 다음 주자가 원할 때 바로 시작할 수 있는 구조라고 할 수 있습니다.** 이전 주자(메모리)는 다음 주자(CPU)보다 확실하게 느리지만 경기 시작도 전에 미리 달려 바톤 터치만 할 수 있는 상황을 만들어 놓는다면 속도는 크게 상관이 없을 것입니다. 컴퓨터 속 세상은 육상 대회가 아니니 딱히 반칙이라고 주장할 사람도 없을 것입니다.

유니티에서 Object Pooling은 메모리에 의해 발생되는 최적화 문제를 최대한 개선하기 위해 미리 여러개의 게임 오브젝트들을 생성하는 방식을 사용합니다. 메모리는 시피유보다 확실하게 느리기 때문에 메모리에 접근하는 행위는 사람이 체감할 수 있을 정도의 시간을 소요할 수 있습니다(프리징). 게임이 진행되기 전 게임 오브젝트를 미리 생성하면 실시간으로 메모리에 접근하는 횟수를 감소시켜 유저가 느끼는 프리징 현상을 예방할 수 있습니다. 인스턴스의 삭제도 마찬가지입니다. C#은 가비지 컬렉터를 사용하여 자동으로 메모리를 관리합니다. 가비지 컬렉터가 작동하면서도 많은 비용을 소모하게 되는데, 순간적으로 많은 오브젝트가 삭제되는 구간에는 프리징이 발생할 수 있습니다. Object Pool에서는 해당 게임 오브젝트를 삭제하지 않고 비활성화 하는 방법으로 메모리로의 접근을 최소화 하고 있습니다.

https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/GlobalManager/TGObjectPoolManager.cs

해당 링크는 프로젝트에서 Object Pooling을 구현하기 위해 작성한 소스코드입니다. 중복되는 메소드를 최소화하고, 여러 인스턴스에서 같은 게임 오브젝트를 생성하기 원할 수 있기 때문에 싱글톤으로 구현된 매니저를 활용할 수 있도록 작성하였습니다. 또한, 유니티에서 기본적으로 제공하는 "ObjectPool"을 활용하였습니다.
필요에 따라 "CreateTGObjectPool"을 사용하여 Object Pool을 생성할 수 있으며, "GetTGObject"와 "ReleaseTGObject"를 호출하여 객체를 활성/비활성화 할 수 있습니다.

## 이벤트 매니저(Observer 패턴)
초당 프레임(FPS)란 간단하게 현재 화면에서 다음 화면으로 전환되는 순간이 1초에 몇 번 일어나는가로 정의할 수 있습니다. FPS의 값이 높을 수록 화면은 더 부드럽고 자연스럽게 느껴질 것입니다. 
게임은 사진을 빠르게 전환할 뿐인 필름영화와는 다르게 3차원의 데이터를 우리가 이해할 수 있는 2차원으로 전환한 다음, 화면에 갱신하는 과정을 포함하고 있습니다. 뿐만 아니라, 게임속의 여러 데이터를 주고 받고, 읽고 쓰고 수 많은 과정을 거친 다음에야 한 화면이 생성되게 됩니다. 그렇다면 다음 화면으로 전환하기 위해서 어떤 과정을 거치고 있는지 알 수 있는 방법이 있을까요? 방식에 따라 다르겠지만 Unity는 해당 문서를 통해 이를 안내하고 있습니다.

https://docs.unity3d.com/kr/2022.3/Manual/ExecutionOrder.html

즉, 우리가 유니티 엔진을 사용하여 게임을 개발한다면 위 문서의 과정을 항상 거친다는 것을 의미하며, 개발자는 생명주기를 고려하여 게임을 개발해야 합니다. 

한 화면을 그려내기 위해 수많은 과정을 거친다는 것을 알게 된다면 Update같은 매 프레임마다 호출되는 명령을 최소화 해야한다는 것을 자연스럽게 깨닫게 됩니다. 명령의 수가 점점 많아질 수록 FPS가 줄어드는 것은 당연한 결과이기 때문입니다. 그런데, 예를들어 개발을 하다보면 어떤 값의 변화를 체크해야하는 순간이 존재할 수 있습니다. 내 캐릭터의 체력이 감소했을 때 UI에 반영해야하는 것 처럼 말입니다. 하지만 값의 변화를 체크해야 하는 게임 오브젝트의 수가 많아진다면 정말 곤란해질 것입니다. Update처럼 한 프레임마다 호출되는 메소드를 늘리는 것은 바람직하지 않다는 것을 알았으니 변화를 체크해야 하는 모든 오브젝트를 레퍼런싱 해야할까요? 체크가 필요한 오브젝트가 정말 많다면 마찬가지로 곤란할 것입니다.

Observer 패턴을 활용한 이벤트 매니저는 이 문제를 해결하기 아주 좋은 방법입니다. 한 객체의 상태가 바뀌면 그 객체에 의존하는 다른 객체에게 메세지를 전달하는 특성을 사용하여 이벤트 매니저를 만들면 레퍼런싱하지 않고도 이벤트를 구독하고 있는 인스턴스들에게 자동으로 값을 전달할 수 있기 때문입니다. 이로써 강한 결합을 하지 않고도 값의 변화를 체크할 수 있으며, 메소드를 실행할 수 있습니다.

이벤트의 구분은 "EEventType"이라는 enum 클래스를 작성하여 활용하였습니다. 해당 enum에 이벤트를 작성하여 구분할 수 있습니다.
```

    // 딕셔너리를 사용하여 이벤트 타입과 해당 델리게이트를 저장
    private Dictionary<EEventType, Action<object>> eventDictionary = new Dictionary<EEventType, Action<object>>();
 ```
 해당 Dictionary를 활용하여 이벤트와 delegate를 저장합니다. 이벤트를 트리거할때 EEventType을 사용하여 상황에 맞는 delegate를 호출하게 됩니다.
 ```
 
    // 이벤트 트리거
    public void TriggerEvent(EEventType eventType, object parameter = null)
    {
        Action<object> thisEvent = null;
        if (eventDictionary.TryGetValue(eventType, out thisEvent))
        {
            thisEvent.Invoke(parameter);
        }
    }
 ```
 이벤트 트리거입니다. 필요 시 매개변수를 기입할 수 있도록 object형 파라미터를 제공하고 있습니다. 해당 트리거에 이벤트 타입을 기입하여 호출하면 리스닝 중인 메소드가 실행됩니다.
 
 ```
  // 이벤트리스닝 시작
 public void StartListening(EEventType eventType, Action<object> listener)
 {
     Action<object> thisEvent;
     if (eventDictionary.TryGetValue(eventType, out thisEvent))
     {
         thisEvent += listener;
         eventDictionary[eventType] = thisEvent;
     }
     else
     {
         thisEvent += listener;
         eventDictionary.Add(eventType, thisEvent);
     }
 }
 ```
 이벤트 리스너입니다. 이벤트 타입과, 실행될 메소드를 파라미터에 작성하면 이벤트 트리거가 발동할 때 마다 해당 메소드가 실행됩니다.
 ```
    // 이벤트리스닝 중지
    public void StopListening(EEventType eventType, Action<object> listener)
    {
        Action<object> thisEvent;
        if (eventDictionary.TryGetValue(eventType, out thisEvent))
        {
            thisEvent -= listener;
            eventDictionary[eventType] = thisEvent;
        }
    }
  ```
 
 이벤트 리스너를 중지합니다. 게임 오브젝트가 삭제될 때 활용됩니다.
 
 https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/GlobalManager/TGEventManager.cs
 
 ## 인벤토리 UI 구현
 해당 인벤토리의 최종적인 목표는 바닥에 떨어져있는 아이템에 상호작용하여 인벤토리로 옮기는 작업을 수행하는 것과 캐릭터가 소지 중인 아이템을 UI에 표시하는 것입니다.![](/assets/images/old/1e4b616e-e973-4ac2-8dee-5439ff8c530c-image.png)
![](/assets/images/old/5ccc36e3-46a1-4e8e-b1da-f73f7240a1ea-image.png)

아이템 프리팹은 ItemModel과 ItemLootRadius를 갖게 됩니다. 여기서 "ItemLootRadius"는 플레이어 캐릭터가 아이템 주변에 존재할 때 인식할 수 있도록 하는 역할을 합니다. Collider의 Trigger를 활용합니다. 이 범위가 넓어질 수록 캐릭터가 상호작용할 수 있는 범위가 넓어지게 됩니다. 이 값은 기획에 따라 변경하여 사용합니다.

![](/assets/images/old/065c7dbc-246c-4f5a-ba86-e1b6d878ea11-image.png)
두 개의 리스트 뷰에서 왼쪽에는 상호작용 가능한 아이템이 표시되고, 오른쪽에는 소지중인 아이템이 표시됩니다. 버튼을 생성할 때에는 앞서 말씀드렸던 ObjectPool이 사용됩니다. 상호작용 가능한 아이템이 갱신될 때 프리징이 유발될 수 있기 때문입니다.
![](/assets/images/old/d1e8a128-afaa-4916-9c0c-0aa488ba0583-image.png)
아이템과 상호작용하여 버튼이 생성된 모습입니다. 해당 버튼을 클릭하면 이벤트 트리거가 발동하여 여러 게임 오브젝트들에 값을 전달하게 됩니다. 아래는 전체 시연 영상입니다.
![](/assets/images/old/1eea0a03-a136-462a-96b7-0728867ba3e7-image.webp)


