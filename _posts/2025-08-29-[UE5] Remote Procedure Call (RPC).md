---
title: "[UE5] Remote Procedure Call (RPC)"
description: "RPC란, UFUNCTION에 네트워킹 플래그를 달아 네트워크 너머에서 함수가 실행되도록 하는 메커니즘입니다. 멀티플레이 게임을 만들 때 Server-Client간 통신을 간단하게 처리할 수 있게 만들어줍니다."
date: 2025-08-29T10:47:56.627Z
tags: ["UE5","C++"]
categories: [C++]
---
RPC란, UFUNCTION에 네트워킹 플래그를 달아 네트워크 너머에서 함수가 실행되도록 하는 메커니즘입니다. 멀티플레이 게임을 만들 때 Server-Client간 통신을 간단하게 처리할 수 있게 만들어줍니다.

이때, RPC를 호출하려면 Replicates가 반드시 true여야 하고, Ownership과 Relevancy 규칙을 따라야 합니다.

# RPC의 종류
### 1. Server RPC
- 선언: UFUNCTION(Server, Reliable/Unreliable)
- 호출: 클라이언트 → 서버
- 실행: 서버에서 실행
- 조건: 호출하는 클라이언트가 액터의 소유자(Owner) 여야 함
- 용도: 입력 전달(총 발사, 점프 등), 서버 권위 판정, 게임 규칙 변경
```cpp
// MyCharacter.h
UCLASS()
class AMyCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    // 클라 → 서버 발사 요청
    UFUNCTION(Server, Reliable)
    void ServerFire(const FVector_NetQuantize& AimDir);

private:
    void InputFire();
};

// MyCharacter.cpp
void AMyCharacter::InputFire()
{
    // 클라는 발사 버튼 누르면 서버에 발사 요청
    if (!HasAuthority()) 
    {
        ServerFire(GetControlRotation().Vector());
    }
}

void AMyCharacter::ServerFire_Implementation(const FVector_NetQuantize& AimDir)
{
    // 서버 권위로 발사 판정
    UE_LOG(LogTemp, Log, TEXT("Server: 발사 처리 중"));

    // 예시: 라인 트레이스 → 적중 판정 → 상태 갱신
}

```
### 2. Client RPC (Run on Owning Client)

- 선언: UFUNCTION(Client, Reliable/Unreliable)
- 호출: 서버 → 특정 클라이언트
- 실행: 해당 액터의 소유 클라이언트에서 실행
- 용도: 서버에서 판정 후 특정 플레이어에게만 보여줄 UI/이펙트 (e.g. 히트마커, HUD 알림)
```cpp
UCLASS()
class AMyCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    // 서버 → 클라: 히트마커 보여주기
    UFUNCTION(Client, Unreliable)
    void ClientShowHitMarker();
};

// MyCharacter.cpp
void AMyCharacter::ClientShowHitMarker_Implementation()
{
    // 해당 플레이어의 클라이언트에서만 실행
    UE_LOG(LogTemp, Log, TEXT("Client: 히트마커 표시"));

    // 예시: HUD Widget에서 히트마커 이미지 표시
}
```

### 3. NetMulticast RPC
- 선언: UFUNCTION(NetMulticast, Reliable/Unreliable)
- 호출: 서버만 호출 가능
- 실행: 서버 + 모든 관련 클라이언트
- 주의: 액터가 클라이언트와 관련성(Relevancy) 있어야 전달됨
- 용도: FX, 사운드, 애니메이션 등 연출 동기화
```cpp
UCLASS()
class AMyCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    // 서버 → 모든 클라: 총구 이펙트 재생
    UFUNCTION(NetMulticast, Unreliable)
    void MulticastPlayMuzzleFX();
};

// MyCharacter.cpp
void AMyCharacter::MulticastPlayMuzzleFX_Implementation()
{
    UE_LOG(LogTemp, Log, TEXT("모든 클라: 총구 이펙트 실행"));

    // 예시: 파티클/사운드 실행
    // UGameplayStatics::SpawnEmitterAttached(MuzzleFlash, MeshComp, TEXT("MuzzleSocket"));
}
```

예시로 총구 이펙트를 제시하긴 했지만, 플레이어의 반응성을 고려하면 발사 입력이 된 동시에 클라이언트에서는 이미 이펙트가 클라이언트 내에서 실행되고 있고, 서버에서 발사 로직이 실행되기 전에 Multicast를 통해 다른 클라이언트에 이펙트 재생 명령이 이뤄져야 한다고 생각합니다. 또한, 해당 방법은 카운터 스트라이크와 발로란트에도 적용되어 있습니다. (클라이언트 내에서의 궤적은 상대 캐릭터를 뚫고 지나갔지만, 실제로 맞지 않는 이유)

# Reliable vs Unreliable
- **Reliable:** 반드시 도착. 순서 보장. → 중요한 이벤트 (매치 시작/종료, 인벤토리 변경)
- **Unreliable:** 손실될 수 있음. → 잦은 FX/사운드 (총구 섬광, 파티클)

# Ownership & Relevancy
- 소유자(Owner): 보통 PlayerController → Pawn/Character → 부착 컴포넌트들
	- Server RPC는 소유한 클라이언트만 호출 가능
	- Client RPC는 서버가 소유자 클라이언트에게만 보냄

- 관련성(Relevancy): 클라이언트가 해당 액터를 “관심 대상”으로 볼 때만 데이터 전달됨
	- NetMulticast도 관련성 없으면 전달 안 됨 → 전역 알림은 GameState 사용 권장
