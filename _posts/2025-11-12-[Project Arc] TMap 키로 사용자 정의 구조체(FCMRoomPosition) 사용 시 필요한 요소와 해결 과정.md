---
title: "[Project Arc] TMap 키로 사용자 정의 구조체(FCMRoomPosition) 사용 시 필요한 요소와 해결 과정"
description: " 컴파일 단계에서 TMap 키 타입에 대한 해시 함수와 동등 비교 연산자가 없다는 오류가 발생했고, 이로 인해 빌드가 진행되지 않았습니다. 본 문서에서는 오류가 발생한 원인과 이를 해결하기 위해 적용한 코드 변경 사항을 정리했습니다."
date: 2025-11-12T03:42:47.783Z
tags: ["project arc","ue5","트러블슈팅"]
image:
  path: /assets/images/old/b3716209-0ace-4ab4-bfc6-171a11810fe9-image.png
categories: [Project CM + Project Arc]
---
절차적 맵 생성 기능을 구현하면서, 격자 좌표를 기반으로 중복 지형 생성을 방지하고 좌표로 즉시 방(Room) 포인터에 접근하기 위해 TMap의 키로 FCMRoomPosition 구조체를 사용하고자 했습니다. 그러나 컴파일 단계에서 TMap 키 타입에 대한 해시 함수와 동등 비교 연산자가 없다는 오류가 발생했고, 이로 인해 빌드가 진행되지 않았습니다. 본 문서에서는 오류가 발생한 원인과 이를 해결하기 위해 적용한 코드 변경 사항을 정리했습니다.

---

## 증상(오류 메시지/현상)
![](/assets/images/old/b3716209-0ace-4ab4-bfc6-171a11810fe9-image.png)

- TMap<FCMRoomPosition, ...> 사용 시 컴파일 오류 발생
- 대표 오류 형태
  - ‘GetTypeHash’: 일치하는 오버로드된 함수가 없습니다 (no matching overloaded function found)
  - TMap 키 타입에 대해 해시를 찾을 수 없습니다 (no hash function for type ‘FCMRoomPosition’)
- 문제 구문 예시
  - TMap<FCMRoomPosition, TObjectPtr<ACMRoom>> Rooms;
  
---
  
## 원인 분석

- TMap은 해시 컨테이너로서 키의 해시 함수가 필요함
- 사용자 정의 USTRUCT 키는 기본 해시가 제공되지 않음
- 전역 범위의 GetTypeHash(const FCMRoomPosition&) 미구현
- 키 동등성 판단을 위한 operator== 미구현 또는 const/시그니처 부적합
- 헤더 분리 시 가시성 문제로 인해 TMap 선언 시점에 GetTypeHash 심볼이 보이지 않는 경우도 발생 가능

---

## 해결
- FCMRoomPosition에 const operator== 정의
- 전역 범위에 FORCEINLINE GetTypeHash(const FCMRoomPosition&) 구현
- 좌표형 int32에 대해 HashCombine(::GetTypeHash(X), ::GetTypeHash(Y)) 사용
- 키/해시 정의가 TMap 선언보다 먼저 포함되도록 include 순서 정리
- 빌드/리빌드로 오류 제거 확인

---
  
## 적용 코드
```cpp
USTRUCT()
struct FCMRoomPosition
{
    GENERATED_BODY()

    int32 X;
    int32 Y;

    FORCEINLINE FCMRoomPosition() : X(0), Y(0) {}
    FORCEINLINE FCMRoomPosition(int32 InX, int32 InY) : X(InX), Y(InY) {}

    FORCEINLINE bool operator==(const FCMRoomPosition& Other) const
    {
        return X == Other.X && Y == Other.Y;
    }
};

// 전역 해시 함수
FORCEINLINE uint32 GetTypeHash(const FCMRoomPosition& Pos)
{
    // 두 좌표 해시 결합
    return HashCombine(::GetTypeHash(Pos.X), ::GetTypeHash(Pos.Y));
}
```
---
  
이번 이슈는 TMap이 요구하는 키 타입 계약(operator==, GetTypeHash)을 간과해서 발생한 문제였습니다. 사용자 정의 구조체를 컨테이너의 키로 사용하려면 비교와 해시의 정의가 반드시 필요하다는 점을 다시금 확인했습니다. 향후에는 키 타입을 설계할 때 동등성/해시의 일관성과 가시성(선언 순서)까지 함께 점검하여 유사한 빌드 오류를 사전에 방지해야겠습니다.

