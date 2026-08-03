---
title: "[Project OnlyOne] 프로젝트 시작"
description: " Last Man Standing 스타일의 술래잡기 프로젝트를 시작합니다."
date: 2025-09-08T11:30:47.442Z
tags: ["project onlyone","ue5"]
image:
  path: /assets/images/old/2216c896-cabf-47ff-9d1a-5d3aaed2cf6d-image.png
categories: [Project OnlyOne]
---
# 프로젝트 요약
- **프로젝트 명:** Only One
- **장르:** Last Man Standing 스타일의 술래잡기
- **팀 인원:** 5명
- **기간:** 2025/09/08 ~ 2025/10/16
- **환경:** Unreal 5.5.4 

# 맡은 역할
 - 팀장
   - 코드 리뷰
   - 회의 진행
   - 깃 관리
   - 노션 관리
 - 프로젝트 생성 및 초기 세팅
 - UI 및 코드 병합
 
     

# 초기 세팅
### 멀티플레이용 Log 매크로 구현

```cpp

#define LOG_LOCALROLEINFO *(UEnum::GetValueAsString(TEXT("Engine.ENetRole"), GetLocalRole()))
#define LOG_REMOTEROLEINFO *(UEnum::GetValueAsString(TEXT("Engine.ENetRole"), GetRemoteRole()))
#define LOG_SUBLOCALROLEINFO *(UEnum::GetValueAsString(TEXT("Engine.ENetRole"), GetOwner()->GetLocalRole()))
#define LOG_SUBREMOTEROLEINFO *(UEnum::GetValueAsString(TEXT("Engine.ENetRole"), GetOwner()->GetRemoteRole()))

#define LOG_NETMODEINFO ((GetNetMode() == ENetMode::NM_Client) ? *FString::Printf(TEXT("CLIENT%d"), (int32)GPlayInEditorID) : ((GetNetMode() == ENetMode::NM_Standalone) ? TEXT("STANDALONE") : TEXT("SERVER"))) 
#define LOG_CALLINFO ANSI_TO_TCHAR(__FUNCTION__)
#define LOG_NET(LogCat, Verbosity, Format, ...) UE_LOG(LogCat, Verbosity, TEXT("[%s][%s/%s] %s %s"), LOG_NETMODEINFO, LOG_LOCALROLEINFO, LOG_REMOTEROLEINFO, LOG_CALLINFO, *FString::Printf(Format, ##__VA_ARGS__))
#define SUBLOG_NET(LogCat, Verbosity, Format, ...) UE_LOG(LogCat, Verbosity, TEXT("[%s][%s/%s] %s %s"), LOG_NETMODEINFO, LOG_SUBLOCALROLEINFO, LOG_SUBREMOTEROLEINFO, LOG_CALLINFO, *FString::Printf(Format, ##__VA_ARGS__))

DECLARE_LOG_CATEGORY_EXTERN(POLog, Log, All);
```

## 폴더 구조 생성
![](/assets/images/old/bbeabbbd-f981-49fe-9039-528e7b3597cb-image.png)


## GameplayTags 초기화
```cpp
class FOnlyOneModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override
	{
		// 부모 클래스의 StartupModule 호출
		FDefaultGameModuleImpl::StartupModule();
		
		// GameplayTags 초기화
		FPOGameplayTags::InitializeNativeTags();
	}
	
	virtual void ShutdownModule() override
	{
		// 부모 클래스의 ShutdownModule 호출
		FDefaultGameModuleImpl::ShutdownModule();
	}
};
```

# 협업 관리
### 노션 기반 협업 관리
![](/assets/images/old/2216c896-cabf-47ff-9d1a-5d3aaed2cf6d-image.png)
- 매일 데일리 스크럼 진행
- 회의록은 녹음 후 AI를 사용하여 회의록 작성 (녹음 -> 텍스트 변환 -> GPT 요약)

### 칸반 보드 
![](/assets/images/old/eb87e0c4-9334-4066-a9bc-a03316fad4a8-image.png)
-

### 코드 컨벤션 및 Github Rule 지정
![](/assets/images/old/702fd525-a6a1-4dac-935a-fb7df67909cc-image.png)
