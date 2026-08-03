---
title: "[TPS프로젝트] (1) Player character movement와 Camera"
description: "3인칭 백뷰 방식의 시점은 Unity에서 어떻게 구현할 수 있을까요? 플레이어 캐릭터의 움직임은 어떻게 구현하며 어떻게 유동적으로 할당 키를 변경할 수 있을까요?"
date: 2024-05-31T14:41:20.181Z
tags: ["C#","Unity"]
thumbnail: /assets/images/old/c87b9a2c-2c10-454c-a94e-95d82c42b777-image.webp
categories: [TPSProject]
---
![](/assets/images/old/51647036-16d8-46c8-9f88-5cd0c98eb514-image.webp)

3인칭 백뷰 슈팅게임의 대표작 '배틀그라운드'의 게임 플레이 영상입니다. 키보드를 입력하여 캐릭터를 움직일 수 있으며 이때 카메라는 캐릭터를 따라다닙니다. 또한, 마우스를 움직이면 캐릭터를 중심으로 카메라가 회전하여 화면이 움직입니다. 이 일련의 카메라 무빙을 통해 플레이어들은 자신이 캐릭터를 직접 조종한다는 느낌을 받게되며, 총을 발사할 때 직접 조준하고 발사한다고 생각하게 됩니다. 그럼 Unity에서 해당 기능을 직접 구현하기 위해선 어떻게 해야할까요?

## 마우스를 통한 카메라 회전
마우스는 기본적으로 2차원으로만 움직일 수 있습니다. 책상 위에서 마우스를 조정할 때 상하좌우의 움직임을 읽어들이는데 반해, 마우스의 센서가 공중에 뜨는 것 까지는 인식(컴퓨터에 값을 전달)하지 않기 때문입니다. 하지만 카메라는 3축으로 이동, 회전할 수 있습니다. 오직 바닥면의 변화를 읽어들이는 마우스와 다르게, 카메라는 3차원 공간에서 존재하는 오브젝트이기 때문입니다. 따라서 마우스로 카메라를 조절하기 위해서는 2개의 축만을 이용하여 회전해야 합니다.

카메라의 회전을 구현하는 것은 매우 간단합니다. 위에 서술했듯이 2개의 축을 활용하여 회전을 시키면 되는데, Unity를 기준으로 y축을 회전시키면 좌우로 회전하고 x축을 회전시키면 위아래로 회전하기 때문입니다. 즉, 마우스의 좌우 움직임은 y축을 회전시키고, 상하 움직임은 x축을 회전시키면 카메라는 우리가 생각하는 것 처럼 자연스럽게 회전하게 됩니다.
![](/assets/images/old/c87b9a2c-2c10-454c-a94e-95d82c42b777-image.webp)

하지만 이 것으로는 예시로 들었던 영상처럼 카메라를 움직일 수 없습니다. 카메라는 아직 고정된 상태이며 우리가 원하는 것은 캐릭터를 카메라가 따라다니며, 마우스를 움직일 때 캐릭터를 중심으로 카메라가 회전하는 것입니다. 그렇다고 카메라를 캐릭터 Position에 고정하면 1인칭 시점이 되거나 머리 위에서 회전하는 CCTV가 될 것입니다.

카메라가 바라보는 방향에 긴 막대를 만들어보겠습니다.
![](/assets/images/old/d80bd7d0-2048-406f-b51e-ad203b53d4e5-image.webp)

저 막대를 셀카봉처럼 플레이어 캐릭터에 붙여서 회전시킨다면 3인칭을 구현할 수 있지 않을까요? 아주 간단한 수학을 이용하여 구현할 수 있습니다. Vector를 사용하여 Target과 Camera가 바라보는 방향을 마이너스 연산하면 해당 사진과 같은 Vector가 생성되게 될 것입니다. 이 값은 셀카봉 역할을 하게 될 것입니다.
![](/assets/images/old/5b1e40e4-a768-4d73-bebe-b06c8451bb6f-image.png)

이제 셀카봉을 매달 수 있게 되었으니 셀카봉의 기본 높이와 길이만 정해주면 완성됩니다.
아래 영상은 구현된 3인칭의 모습입니다.
![](/assets/images/old/9896e828-aa04-462d-b0e9-240f79c77393-image.webp)
![](/assets/images/old/f00f2896-aad1-48eb-be6a-9a0e51e83e29-image.webp)

카메라와 캐릭터간의 거리는 마우스 휠로 조절할 수 있도록 구현하였습니다. 또한, 게임을 하다보면 UI를 사용하거나 하는 등의 이유로 마우스 커서를 사용해야 하는 경우가 많기 때문에 특정 키를 입력하면 마우스 잠금이 해제되도록 구현하였습니다. 아래는 카메라 무빙을 구현한 소스코드입니다.

https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/Game/Camera/TGPlayerFollowMainCameraController.cs

## 키보드 입력을 통한 캐릭터 이동
Unity에서 가장 대표적인 키 입력 메소드는 Input.GetKey일 것입니다. GetKey를 사용하여 조건문을 작성하면 키 입력을 감지하여 원하는 명령을 내 게임에게 내릴 수 있습니다. 하지만 GetKey만을 사용하여 조건문을 작성하게 되면 아래 사진 처럼 유저가 커스텀한 키를 사용하는 것은 사실상 불가능에 가까울 것입니다.
![](/assets/images/old/bb850d6b-c0e4-4d72-adbe-2aa73cde755e-image.png)

저는 이를 해결하기 위해 TGPlayerKeyManager라는 클래스를 만들어서 해결하였습니다. 해당 클래스파일에는 내 게임에서 사용할 키 입력들의 enum 값들이 포함되어있습니다. 또한, Input.GetKey에서 입력된 키보드 값이 무엇인지 분류해놓은 KeyCode를 Dictionary로 묶어 호출할 수 있도록 구현하였습니다. 이렇게 작성한 클래스를 싱글턴화 시켜 하나의 인스턴스로 관리하면, 키 입력을 받아야 하는 클래스를 만들 때 쉽게 호출하여 사용할 수 있습니다.

https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/GlobalManager/TGPlayerKeyManager.cs

초기값을 셋팅하는 것은 파일을 이용하여 초기화 하는 것으로 대체될 예정입니다.
KeyChange는 위 사진처럼 커스텀 키 설정 옵션을 구현할 때 호출될 것입니다.


이제 유동적으로 필요한 키 코드를 변경할 수 있게 되었으니 해당 클래스를 이용하여 내 캐릭터를 이동시킬 수 있는 소스코드를 작성해보겠습니다.

https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/Game/Unit/PlayerCharacter/TGPlayerCharacter.cs
https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/Game/Unit/PlayerCharacter/TGPlayerCharacterController.cs

카메라 방향에 따라 캐릭터가 회전할 수 있는 기능과 그냥 움직이면 심심하니 파라미터에 따라 애니메이션이 재생될 수 있도록 구현하였습니다. 아래 영상은 완성된 캐릭터의 움직임입니다.
![](/assets/images/old/1dd6e05f-0eae-41a0-aa24-8ed5bdcac6a2-image.webp)

