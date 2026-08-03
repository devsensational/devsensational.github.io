---
title: "[Project OnlyOne] Listen Server를 활용한 테스트 환경 구축"
description: "해당 프로젝트는 Dedicated Server를 사용할 것이기 때문에, 테스트가 필요할 때 마다 패키징을 해야 했습니다. 자동화된 패키징 환경이 구축되어 있지 않기 때문에 생산성에 큰 문제를 야기했습니다."
date: 2025-09-15T11:38:25.610Z
tags: ["project onlyone","ue5"]
image:
  path: /assets/images/old/f212b4f4-f6d6-4fbf-81a6-4f0fea582564-image.webp
categories: [Project OnlyOne]
---
![](/assets/images/old/f212b4f4-f6d6-4fbf-81a6-4f0fea582564-image.webp)
해당 프로젝트는 Dedicated Server를 사용할 것이기 때문에, 테스트가 필요할 때 마다 패키징을 해야 했습니다. 자동화된 패키징 환경이 구축되어 있지 않기 때문에 생산성에 큰 문제를 야기했습니다. 따라서, 프로젝트의 원활한 테스트를 위한 환경을 Listen Server로 구축하였습니다.  

# 주요 구현 내용
### UI 구조 변경
- **POMainMenuWidget**: 메인 메뉴에 "Host Server" 버튼이 추가됨
- **POHostServerWidget**: 서버 호스팅을 위한 새로운 UI 위젯 생성
- 사용자명 입력을 위한 **EditableTextBox** 컴포넌트 포함

### 컨트롤러 기능 확장
- **APOMainMenuPlayerController**에 다음 기능들이 추가됨:
- **ShowHostServer()**: 호스트 서버 UI를 표시하는 함수
- **OnHostServer()**: 실제 서버 호스팅 로직을 처리하는 함수
- **FJoinServerData** 구조체를 통한 서버 정보 관리

# 구현 방식
- **UI 플로우**: MainMenu → HostServerWidget → 사용자명 입력 → 호스팅 시작
- **레벨 전환**: UGameplayStatics::OpenLevel을 통해 "listen" 옵션으로 서버 로비 레벨로 이동
- **프로필 관리**: GameInstance에 사용자 정보 저장

# 마치며
아직 네트워크 실패 처리나, 서버 설정 옵션이 제한적인 부분이 있습니다. 그 부분을 좀 더 보완하도록 노력해야 겠습니다.