---
title: "[토이프로젝트] Character의 Physics Simulation 문제와 최적화 시도 (캐릭터 충돌 시 떨림 문제)"
description: "언리얼에서 제공하는 Character Movement 클래스를 사용한 액터가 다른 액터와 부딪히면 위 영상과 같이 캐릭터가 떨리는 문제가 발생합니다."
date: 2025-07-08T10:13:14.122Z
tags: ["UE5","토이프로젝트"]
thumbnail: /assets/images/old/62ed1635-8f03-44ea-8312-a77073fd20a4-image.webp
---
# 문제 발생과 원인
![](/assets/images/old/62ed1635-8f03-44ea-8312-a77073fd20a4-image.webp)
![](/assets/images/old/5509d7cd-4e69-4ad0-8b9a-a5b2c523c227-image.webp)

언리얼에서 제공하는 Character Movement 클래스를 사용한 액터가 다른 액터와 부딪히면 위 영상과 같이 캐릭터가 떨리는 문제가 발생합니다. (영상에 잘 담기진 않지만 캐릭터는 매우 빠른속도로 진동하고 있습니다)

![](/assets/images/old/47aaee32-1666-49b4-a41d-deb10ef68693-image.webp)
하지만 캐릭터가 움직이는 상태에서는 문제가 발생하지 않는다는 것을 알 수 있습니다. 왜 그럴까요?

 **언리얼에서 제공하는 Character Movement Component가 움직일 때에만 Physics simulation을 실행하고 가만히 있을 때는 실행하지 않기 때문입니다.**
 
 
 # 편법 같은 해결 방법? 개선할 수 있을까?
 여러 채널에서 도움을 받은 결과, **캐릭터를 강제로 이동 중인 상태로 만들어 Physics Simulation 중인 상태로 만드는 방법이 가장 유력했습니다.** 
 
 ![](/assets/images/old/e3fbfca7-9de3-4f98-9d15-f5e53a0e19d2-image.png)

해당 사이드 프로젝트에도 적용해보니 캐릭터의 떨림 문제가 완전히 해결되었습니다. 하지만 필요하지 않은 상황에서도 시뮬레이션이 계속해서 수행되고 있으며, Tick에서 계속 캐릭터를 이동시키고 있으므로 퍼포먼스에 악영향을 줄 것은 분명합니다.

# 최적화
그래서 저는 캐릭터의 위치에 영향을 줄 수 있는 'Platform' 액터들이 주변에 있을 때에만 물리 연산을 수행하도록 변경하는 것을 계획했습니다. 캐릭터에 Platform을 감지할 수 있는 Collision을 추가하고, 이 Collision에 오버랩되면 시뮬레이션이 시작되도록 할 것입니다.
![](/assets/images/old/c86a3925-d069-4b74-94bd-a3ec82f63f80-image.png)
먼저 'Platform'이라는 이름의 Object Channel을 추가했습니다. Default Responese는 Overlap으로 설정했지만 이 두가지 모두 프로젝트에 맞는 방법으로 설정하시면 됩니다. 그 후 캐릭터에 부착된 박스 콜라이전을 아래 프리셋 처럼 지정합니다. 상세한 설정은 프로젝트에 맞게 진행하시면 됩니다.
![](/assets/images/old/3a4a6677-9286-4695-91d6-8aab53bd2c62-image.png)

PlatformBase 생성자에서 CollisionProfile을 방금 추가한 Preset으로 변경했습니다.
```
// Sets default values
AHWPlatformBase::AHWPlatformBase()
{
	PrimaryActorTick.bCanEverTick = true;
	
	// 플랫폼 메시 컴포넌트 생성
	PlatformMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlatformMesh"));
	PlatformMesh->SetCollisionProfileName(TEXT("Platform"));
	RootComponent = PlatformMesh;
}
```

int OverlapCount 변수를 추가한 후 Overlap 시 카운트가 추가되도록 하고, Overlap이 종료되면 카운트를 감소시킵니다.
![](/assets/images/old/e12aedc1-cd70-4f9f-a813-e2e765ec4fe6-image.png)

카운트를 세는 이유는 다수의 플랫폼이 겹쳤다가 하나의 플랫폼이 빠져나가면 그 즉시 시뮬레이션이 종료되기 때문입니다. 예를 들어, 2개의 플랫폼에 의해 밀리고 있었는데 1개가 사라지면 다시 떨림 문제가 발생합니다.


또한, Branch를 추가하여 OverlapCount가 1 이상일 때에만 시뮬레이션 되도록 설정합니다.
![](/assets/images/old/4c7985fd-f98f-4397-9e76-f3e5c6ff41dc-image.png)


이 방법도 Tick에서 Branch를 계속 호출하고 있기 때문에 성능 저하가 있는 것이 아니냐는 궁금증이 생기실 수 있습니다. Branch(if)의 경우에는 MoveComponent와 비교하면 현저하게 적은 자원을 소모하기 때문에 무시해도 될 만큼의 퍼포먼스 차이를 보여줍니다.

| 항목      | 단순 `if` 문           | `MoveComponent`             |
| ------- | ------------------- | --------------------------- |
| 소요 시간   | 보통 **몇 클럭** (ns 단위) | **수천 \~ 수만 클럭** (us 단위도 가능) |
| 수행 내용   | CPU 레지스터 조건 분기      | 물리 계산, 충돌 검사, 이벤트 호출 등      |
| 성능 영향   | 매우 작음               | 연속 호출 시 프레임 드랍 가능           |
| 주 사용 위치 | 모든 코드               | 주로 **물리 연산**이 필요한 액터 이동     |


퍼포먼스를 비교하기 위해 해당 최적화를 적용한 캐릭터와 아닌 캐릭터를 각각 192개 생성하여 초당 프레임 수를 비교해 보았습니다. 


**최적화 미적용 (약 36 프레임 수준)**
![](/assets/images/old/85c2113c-d2e6-4f86-8ae9-112345caaa95-image.png)

**최적화 적용 (약 51프레임)**
![](/assets/images/old/222f6cf5-9162-48de-b9c0-ec79b58cac8e-image.png)


![](/assets/images/old/c0c5973c-0073-43b9-9c49-2bb465cee8e5-image.webp)
떨림 문제도 동일하게 해결 되었습니다.

# 결론
Character Movement와 같이 엔진에서 제공하는 컴포넌트는 편리하지만, 내부적으로 많은 연산을 포함하고 있어 Tick에서 반복 호출될 경우 큰 성능 저하를 유발할 수 있습니다. 특히 Physics Simulation은 대표적으로 무거운 작업으로, 캐릭터가 가만히 있을 때에도 이를 계속 수행한다면 낭비가 발생합니다.

이번 최적화에서는 단순히 분기(if)문 하나를 추가하는 것만으로도, 필요할 때만 시뮬레이션을 수행하게 하여 떨림 문제를 해결하는 동시에 약 40% 가까운 성능 개선 효과를 확인할 수 있었습니다.

따라서 Tick에서 연산을 수행할 때는 다음을 항상 고려해야 합니다:

- 필요할 때만 동작하게 만들 것
- 충돌 또는 감지 기반으로 조건을 걸 것
- 비용이 큰 연산은 최대한 줄이고 대체 로직을 사용할 것

특히 반복적인 MoveComponent, Physics, Sweep 연산은 꼭 필요한 상황에서만 호출되도록 구조적인 제어가 필요합니다.

결국, 성능 최적화란 무언가를 줄이는 게 아니라, 꼭 필요한 순간에만 실행되도록 바꾸는 작업임을 이번 경험을 통해 다시금 느꼈습니다.