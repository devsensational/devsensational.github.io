---
title: "[UE5/C++] Inline과 FORCEINLINE "
description: "C++의 inline 키워드는 컴파일러에게 함수 호출 시 해당 함수의 코드를 호출 지점에 직접 삽입하도록 요청하는 힌트입니다."
date: 2025-09-05T10:52:37.877Z
tags: ["UE5","C++"]
categories: [C++]
---
## inline의 구조와 원리

C++의 `inline` 키워드는 컴파일러에게 함수 호출 시 해당 함수의 코드를 호출 지점에 직접 삽입하도록 요청하는 힌트입니다. 


### 동작 원리
```cpp
inline int add(int a, int b) {
    return a + b;
}

int main() {
    int result = add(5, 3);  // 컴파일 시 add(5, 3) → 5 + 3으로 치환
    return 0;
}
```

컴파일러는 함수 호출 오버헤드를 제거하고 최적화를 수행합니다. 하지만 `inline`은 어디까지나 **힌트**이므로 컴파일러가 무시할 수 있습니다. 이 동작이 발생할 수 있는 두 가지 경우는 다음과 같습니다.

>
- 재귀 함수
- 변환 단위의 다른 위치에서 포인터를 통해 참조되는 함수

https://learn.microsoft.com/ko-kr/cpp/cpp/inline-functions-cpp?view=msvc-170
## inline의 장점

### 1. 성능 향상
- 함수 호출 오버헤드 제거 (스택 프레임 생성/해제, 점프 명령어 등)
- 컴파일러 최적화 기회 증가

### 2. 타입 안전성
- 매크로와 달리 타입 검사가 수행됩니다
- 스코프 규칙을 따릅니다

### 3. 디버깅 용이성
- 매크로보다 디버깅이 쉽습니다

## 언제 사용하는가?

### 적합한 경우
```cpp
// 1. 간단한 getter/setter
inline int getValue() const { return value; }

// 2. 짧은 연산 함수
inline float square(float x) { return x * x; }

// 3. 템플릿 함수 (헤더에 정의)
template<typename T>
inline T max(T a, T b) { return a > b ? a : b; }
```

### 부적합한 경우
- 복잡하고 긴 함수
- 재귀 함수
- 가상 함수 (대부분의 경우)

## Unreal FORCEINLINE과의 차이점

### FORCEINLINE의 정의
```cpp
// UE5 Core/Public/HAL/Platform.h
#ifndef FORCEINLINE
    #if defined(_MSC_VER)
        #define FORCEINLINE __forceinline
    #elif defined(__GNUC__)
        #define FORCEINLINE inline __attribute__((always_inline))
    #else
        #define FORCEINLINE inline
    #endif
#endif
```

### 주요 차이점

| 구분 | C++ inline | Unreal FORCEINLINE |
|------|------------|-------------------|
| 강제성 | 힌트 (컴파일러가 무시 가능) | 강제 인라인 (컴파일러 지시) |
| 플랫폼 의존성 | 표준 C++ | 플랫폼별 컴파일러 확장 |
| 사용 목적 | 일반적인 최적화 | 성능 크리티컬한 코드 |

### FORCEINLINE 사용 예시
```cpp
// UE5에서 벡터 내적 계산
FORCEINLINE float FVector::DotProduct(const FVector& A, const FVector& B)
{
    return A.X * B.X + A.Y * B.Y + A.Z * B.Z;
}

// 매 프레임 호출되는 간단한 수학 연산에 사용
FORCEINLINE float FMath::Square(float Value)
{
    return Value * Value;
}
```

## 실제 성능 차이

게임 엔진에서는 매 프레임 수천 번 호출되는 간단한 수학 함수들이 있어, `FORCEINLINE`을 통한 강제 인라인이 성능에 큰 영향을 미칩니다. 특히 벡터 연산, 수학 함수, 자주 사용되는 유틸리티 함수에서 그 효과가 두드러집니다.

## 결론

- **C++ inline**: 컴파일러에게 인라인을 제안하는 표준적인 방법
- **Unreal FORCEINLINE**: 성능이 중요한 게임 엔진에서 강제로 인라인을 수행하는 플랫폼별 최적화

게임 개발에서는 프레임레이트가 중요하므로, Unreal Engine처럼 성능 크리티컬한 부분에서는 `FORCEINLINE`을 적극 활용하는 것이 합리적입니다. 하지만 코드 크기 증가와 컴파일 시간 증가라는 트레이드오프를 항상 고려해야 합니다.