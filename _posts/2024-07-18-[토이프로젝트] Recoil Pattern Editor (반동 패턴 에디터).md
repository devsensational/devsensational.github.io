---
title: "[토이프로젝트] Recoil Pattern Editor (반동 패턴 에디터)"
description: "해당 프로젝트는 'TPS프로젝트'의 반동 패턴을 쉽게 생성/수정하고, 스크립트화 하는 것을 목적으로 시작되었습니다.Recoil Pattern Editor는 Unity에서 동작하며, 누구나 쉽게 반동 패턴을 수정하고 스크립트화 할 수 있도록 하는 것이 목적입니다."
date: 2024-07-18T08:54:26.976Z
tags: ["C#","Unity","토이프로젝트"]
image:
  path: /assets/images/old/7d60611f-c2e5-4f05-827d-963480f7e1df-image.png
categories: [사이드프로젝트]
---
해당 프로젝트는 "TPS프로젝트"의 반동 패턴을 쉽게 생성/수정하고, 스크립트화 하는 것을 목적으로 시작되었습니다.

Recoil Pattern Editor는 Unity에서 동작하며, 누구나 쉽게 반동 패턴을 수정하고 스크립트화 할 수 있도록 하는 것이 목적입니다.

# 기능 소개 및 사용 방법
## 전체 메뉴
![](/assets/images/old/cc47be15-78b8-4977-b4ad-6738d22c41a8-image.png)

"Recoil Generator" 스크립트의 Inspector를 사용하여 쉽게 제어할 수 있습니다.

**1. Json File**: Text Asset을 지정할 수 있게 하는 파라미터 입니다. 해당 에디터를 통해 생성된 Json 파일을 지정하면 Load 할 수 있게 합니다.
**2. File Name**: Json 파일을 저장할 때 이름을 지정하는 파라미터입니다.
**3. Save**: 해당 버튼을 클릭하면 에디터에 수정된 사항이 지정된 이름으로 저장됩니다.
**4. Load**: 해당 버튼을 클릭하면 지정한 Json 파일이 로드됩니다.
**5. Point Prefab**: 다음 반동 패턴 포인트를 생성하기 위한 프리팹을 지정합니다.
**6. Point Count**: 반동 패턴의 갯수를 지정합니다.
**7. Apply**: 해당 버튼을 클릭하면 지정된 갯수 만큼의 패턴 포인트가 지정됩니다.

## 사용 방법
1. 먼저 Unity Editor에서 Play 버튼을 클릭합니다.
2. Generator options에서 Point Count를 원하는 만큼 지정합니다. 이 때, 기획한 총의 장탄수 보다 1발 더 많게 지정해야 합니다. (1번 포인트는 아무것도 발사하지 않았을 때 입니다.)
3. 포인트가 생성되면 Secne 창에서 Recoil2 오브젝트 부터 차례대로 이동시켜 원하는 반동 패턴을 만들어 냅니다.

![](/assets/images/old/95dce63e-7cbc-4862-823f-8179f34f23dc-image.png)

4. 이후 이름을 지정한 후 Save 버튼을 클릭하면 Json 폴더에 결과물이 출력됩니다.
![](/assets/images/old/b4f4e429-a6f2-4acc-ad1f-cba66ac562fc-image.png)

5. 결과물에는 다음 포인트까지 x, y축으로 얼마만큼 거리가 벌어져 있는지가 기록됩니다.

## 적용 예제
![](/assets/images/old/13467845-2d7d-40cc-8537-0a4a5424ced0-image.gif)

해당 영상은 TPS프로젝트에 반동 패턴을 적용한 모습입니다. 카메라 반동이 기획과 동일하게 작동하는 모습을 볼 수 있습니다.

해당 리코일 패턴의 적용 소스코드는 다음 링크에서 보실 수 있습니다.

카메라 무빙 관련:
https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/Game/Camera/TGPlayerFollowMainCameraController.cs

반동 로직 관련:
https://github.com/devsensational/3DGameProject/blob/main/3DProject/Assets/Scripts/Game/Item/Weapon/TGItemWeapon.cs