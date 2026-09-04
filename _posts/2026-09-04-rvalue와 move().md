---
title: rvalue와 move()
date: 2026-09-04 16:09 +0900
category: [CPP]
tags: ["cpp"]
description: r-value, move() 함수 내부 구현 정리
math: true
---

### 라이선스 표기

> Copyright (c) Microsoft Corporation.
> SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
> 모든 코드는 표기된 라이센스를 따르며, 설명을 위해 수정된 사항이 있을 수 있습니다.

### 원문 출처
> [https://github.com/microsoft/STL/blob/main/stl/inc/type_traits](https://github.com/microsoft/STL/blob/main/stl/inc/type_traits)
> (https://en.cppreference.com/cpp/utility/move)[https://en.cppreference.com/cpp/utility/move]

---

## 선 요약

| 구분                    | C++11 이전                                               | C++11 이후                                                        |
| ----------------------- | -------------------------------------------------------- | ----------------------------------------------------------------- |
| rvalue 개념             | 존재했음 (값 범주 자체는 원래 있음)                      | 세분화됨 (lvalue / prvalue / xvalue)                              |
| rvalue를 구분할 방법    | 없음 (`const T&`가 lvalue/rvalue 둘 다 받지만 구분 불가) | `T&&`(rvalue reference) 타입으로 구분 가능                        |
| vector 복사/이동        | 항상 깊은 복사 (O(n))                                    | rvalue면 이동 생성자 선택 → 포인터만 교체 (O(1))                  |
| `std::move`의 역할      | (없음)                                                   | 무조건 rvalue로 캐스팅 (개발자가 짠 라이브러리 코드)              |
| `std::forward`의 역할   | (없음)                                                   | 원래 값 범주를 복원해서 캐스팅 (템플릿에서만 의미 있음)           |
| 이동 생성자의 구현 주체 | (없음)                                                   | 단순 타입은 컴파일러 자동 생성, 자원 소유 타입은 개발자 직접 구현 |
| 이름 있는 `T&&` 변수    | —                                                        | 표현식으로 쓰면 항상 lvalue (재캐스팅 필요)                       |

---

## 들어가며

C++에서 값 복사를 막기 위해 `std::move`를 많이 사용합니다. 이 함수의 내부 구현이 궁금해져 들여다 보았는데, 제 생각과는 다른 형태로 구현되어 있었습니다.

```cpp
_EXPORT_STD template <class _Ty>
_NODISCARD _MSVC_INTRINSIC constexpr remove_reference_t<_Ty>&& move(_Ty&& _Arg) noexcept {
    return static_cast<remove_reference_t<_Ty>&&>(_Arg);
}
```

소유권을 이전하기 위한 로직이 아닌, rvalue reference로 캐스팅하는 동작만 구현되어 있었습니다. 이걸 보면서 저의 rvalue에 대한 오해를 깨달았고, rvalue에 대해서 다시 공부하여 왜 `std::move`는 위와 같은 방식으로 구현됬는지 알아보겠습니다.

---

## 값 범주(Value Category): lvalue, prvalue, xvalue

C++에서 모든 표현식(expression)은 **값 범주**를 가집니다. C++11부터는 다음과 같이 세분화됩니다.

```
                  expression
                 /          \
             glvalue       rvalue
             /     \        /    \
         lvalue   xvalue  xvalue  prvalue
```

두 축으로 이해하면 쉽습니다.

|                                    | **정체성(위치)이 있음** | **정체성이 없음** |
| ---------------------------------- | ----------------------- | ----------------- |
| **자원을 뜯어가면 안 됨**          | **lvalue**              | (해당 없음)       |
| **자원을 뜯어가도 안전 (movable)** | **xvalue**              | **prvalue**       |

- **glvalue** = lvalue + xvalue → 특정 객체를 가리키는(주소를 특정할 수 있는) 값
- **rvalue** = xvalue + prvalue → 자원을 이동시켜도 안전한 값
- **xvalue**는 이 둘의 교집합: 정체성은 있지만, 곧 파괴될 예정이라 자원을 뜯어가도 되는 값

### lvalue

이름이 있고, 메모리상의 위치(주소)를 특정할 수 있으며, 표현식이 끝난 뒤에도 계속 존재하는 값.

```cpp
int a = 5;      // a는 lvalue
int* p = &a;    // 주소를 취할 수 있음
```

### prvalue (pure rvalue)

이름이 없고, 아직 어떤 객체로도 실체화(materialize)되지 않은 순수한 "값을 계산해내는 절차" 그 자체.

```cpp
1 + 2;      // prvalue
Foo();       // prvalue (Foo 임시 객체를 만들어내는 표현식)
makeFoo();    // prvalue (함수가 반환하는 임시 객체)
```

### xvalue (eXpiring value)

특정 객체를 가리키긴 하지만(정체성이 있지만), 그 객체의 생명주기가 끝나가는 중이라 자원을 재사용해도 안전한 표현식. `std::move`의 반환값이 대표적입니다.

```cpp
std::string s = "hello";
std::move(s);         // xvalue: s와 같은 위치를 가리키지만, T&&로 캐스팅되어 "곧 버려질 값" 취급
makeFoo().data;         // xvalue: 임시 객체의 멤버 접근 결과
static_cast<Foo&&>(f);   // xvalue: 명시적 캐스팅
```

`makeFoo()` 자체는 prvalue지만, 그 임시 객체의 멤버에 접근하는 순간(`makeFoo().data`) 특정 위치를 가리키게 되므로 xvalue로 바뀝니다. prvalue와 xvalue 둘 다 이동 생성자를 트리거할 수 있다는 점은 같지만, prvalue는 RVO(Return Value Optimization)로 복사/이동 자체가 생략될 수 있는 반면(C++17부터 특정 상황에서 보장됨), xvalue는 이미 실체화된 객체이므로 그런 생략 없이 이동 생성자/이동 대입 연산자가 실제로 호출됩니다.

이 포스트에서는 이후 편의상 prvalue와 xvalue를 묶어 넓은 의미의 "rvalue"로 부르겠습니다.

---

## C++11 이전: 구분할 수 없었기에 항상 복사했다

C++11 이전에도 `const T&`는 lvalue와 rvalue를 모두 받을 수 있었습니다.

```cpp
void foo(const std::vector<int>& v);
foo(makeVec()); // 임시 객체(rvalue)도 const T&로 받을 수 있음
```

문제는 **받은 뒤에 그것이 lvalue인지 rvalue인지 구분할 방법이 없었다**는 것입니다. `const`가 붙어 있어 내부를 변경할 수도 없었고, "이 객체는 곧 사라질 테니 내부 자원을 뜯어가도 안전하다"는 신호를 언어가 전달할 방법이 없었습니다.

그 결과, `vector`, `string` 같은 타입은 항상 **깊은 복사(deep copy)** 를 했습니다. 원소 개수에 비례해서 새 메모리를 할당하고 각 원소를 하나하나 복사 생성했습니다.

---

## C++11 이후: `&&`로 rvalue를 "구분"할 수 있게 되다

C++11은 `T&&`(rvalue reference)라는 새로운 참조 타입을 도입했습니다. 이로써 오버로드 해석(overload resolution)이 인자의 값 범주에 따라 다른 함수를 선택할 수 있게 되었습니다.

```cpp
void bar(const T& x);  // lvalue용: 안전하게 복사
void bar(T&& x);       // rvalue용: 내부 자원을 뜯어가도 안전
```

- 인자가 lvalue면 → `const T&` 오버로드 선택 → 복사
- 인자가 rvalue면 → `T&&` 오버로드 선택 → **개발자가 정의한** 값싼 동작 수행 가능

**컴파일러가 하는 일은 딱 하나입니다: *"이 인자는 rvalue니까 `T&&` 버전을 선택해라."* 그 `T&&` 버전(이동 생성자) 안에 실제로 무엇을 넣을지는 뒤에서 다룰 것처럼 상황에 따라 컴파일러가 자동 생성하거나, 클래스를 설계한 사람이 직접 작성합니다.**

---

## `std::move`는 캐스트일 뿐, 아무것도 옮기지 않는다

`std::move`의 실제 구현은 다음과 같습니다.

```cpp
_EXPORT_STD template <class _Ty>
_NODISCARD _MSVC_INTRINSIC constexpr remove_reference_t<_Ty>&& move(_Ty&& _Arg) noexcept {
    return static_cast<remove_reference_t<_Ty>&&>(_Arg);
}
```

`std::move(x)`는 `x`가 이름 있는 lvalue라 하더라도 그것을 `T&&`로 강제 캐스팅해서, 오버로드 해석이 `T&&` 버전(이동 생성자)을 고르도록 유도할 뿐입니다. 실제 자원 이전은 이 캐스트가 아니라, 그 결과로 선택되는 **이동 생성자/이동 대입 연산자 내부**에서 일어납니다. 컴파일러가 이 캐스트를 인라인 처리하면 어셈블리 상에는 흔적조차 남지 않습니다.

즉, `std::move`가 소유권을 이전하기 위한 로직이 들어있을 것이라고 상상했던 부분은 큰 오해였으며, move semantic이 왜 의미론인지 깨닫게 되는 순간이 이 부분이었습니다. 컴파일러나 언어에서 제공하는 기능을 완전히 뜯어 고친게 아니었습니다. r-value를 구분할 수 있는 방법을 마련함으로써, 퍼포먼스를 개선할 수 있는 여지를 만든 것입니다. 새로운 개념을 위해서 모든 것을 뜯어 고칠 필요가 없었습니다. `&&`이 매개변수로 들어왔을 때 어떤 로직을 구현할지 개발자가 선택만 하면 됩니다. 그래서 `std::move`는 복잡한 로직을 구현할 필요가 없었던 것입니다. `&&T`로 캐스팅만 해주면 rvalue에 대한 처리는 개발자가 만들어 놓았을테니까요. 정말 천재적인 발상 같습니다. 

---

## 그럼 `vector`는 `&&`를 이용해 이동 생성자를 어떻게 구현했나?

`std::vector`는 내부적으로 힙에 할당된 버퍼를 가리키는 포인터 몇 개(시작, 끝, 예약된 끝)로 구성됩니다. 이동 생성자는 이 **포인터만 옮기고 원소는 건드리지 않습니다.**

```cpp
// 개념적으로 표현한 vector의 두 생성자

// 복사 생성자: 항상 존재했음 — 깊은 복사
vector(const vector& other) {
    _Myfirst = allocate(other.size());
    _Mylast  = uninitialized_copy(other._Myfirst, other._Mylast, _Myfirst);
    _Myend   = _Mylast;
}

// 이동 생성자: C++11에서 추가 — 포인터만 교체
vector(vector&& other) noexcept {
    _Myfirst = other._Myfirst;   // 버퍼 소유권을 그대로 가져옴
    _Mylast  = other._Mylast;
    _Myend   = other._Myend;

    other._Myfirst = nullptr;    // 원본은 소유권을 포기
    other._Mylast  = nullptr;
    other._Myend   = nullptr;
}
```

`std::move(v1)`을 호출하면 `v1`이 `vector&&`로 캐스팅되고, 오버로드 해석에서 이동 생성자가 선택되어 위 코드가 실행됩니다. 원소가 100만 개든 1개든 **포인터 3개만 복사**하면 되므로 O(1)입니다. 반면 복사 생성자는 원소 개수에 비례하는 O(n) 깊은 복사입니다.

여기서 한 가지 미묘한 규칙이 있습니다. `other`의 선언 타입은 `vector&&`지만, 함수 본문 안에서 `other`라는 **이름을 표현식으로 쓰는 순간 그것은 lvalue로 취급**됩니다. 그래서 `other._Myfirst = nullptr;`처럼 자유롭게 대입할 수 있는 것이고, 만약 `other`를 다른 함수에 그대로 넘긴다면 그 함수 입장에서는 lvalue로 보입니다. ("타입이 rvalue reference"인 것과 "그 이름의 표현식이 rvalue인 것"은 별개입니다. 이 구분이 뒤에서 다룰 `std::forward`가 필요한 이유의 핵심입니다.)

---

## 참조 붕괴(Reference Collapsing)

### 정의

템플릿 타입 추론이나 `using`/`typedef`, `decltype` 등을 거치면서 "참조에 대한 참조"(reference to reference)가 만들어지는 상황이 생기는데, 이건 문법적으로 직접 쓸 수는 없지만(`int& &x;`는 컴파일 에러) 템플릿 인스턴스화 결과로는 종종 발생합니다. 이때 컴파일러가 정해진 규칙에 따라 이를 **하나의 참조로 합쳐버리는 것**이 참조 붕괴입니다.


| 조합     | 결과  |
| -------- | ----- |
| `T&  &`  | `T&`  |
| `T&  &&` | `T&`  |
| `T&& &`  | `T&`  |
| `T&& &&` | `T&&` |

> &&가 true인 and 연산으로 기억하면 쉬운 것 같습니다.

### 왜 생겼는가

C++11에서 rvalue reference(`&&`)가 도입되면서, **템플릿에서 `T&&`를 매개변수로 쓰는 패턴**(forwarding reference / universal reference)이 필요해졌습니다. 이건 다음처럼 문제를 일으킵니다.

```cpp
template <class T>
void wrapper(T&& x) { /* ... */ }

int a = 5;
wrapper(a);   // a는 lvalue
wrapper(10);   // 10은 rvalue
```

템플릿 타입 추론 규칙상, `wrapper(a)`처럼 **lvalue를 넘기면 `T`는 `int&`로 추론**됩니다. 매개변수 선언 `T&&`에 그대로 대입해보면:

```
T&& → (int&)&&
```

바로 여기서 "참조의 참조"가 만들어집니다. C++11은 이걸 문법 오류로 금지하는 대신 **붕괴 규칙으로 정리**했습니다.

- `wrapper(a)` (lvalue 전달) → `T = int&` → `T&& = int& &&` → 붕괴 → **`int&`** (lvalue reference)
- `wrapper(10)` (rvalue 전달) → `T = int` → `T&& = int&&` → 붕괴 필요 없음 → **`int&&`** (rvalue reference)

이 붕괴 규칙 덕분에 `T&&`라는 **하나의 문법으로 lvalue와 rvalue를 둘 다 받을 수 있는** 매개변수(forwarding reference)가 성립합니다. 이게 참조 붕괴가 필요했던 근본 이유이고, 바로 다음에 다룰 완벽한 전달의 토대가 됩니다.

---

## `std::move` vs `std::forward`

둘 다 "캐스트일 뿐, 아무것도 옮기지 않는다"는 점은 동일합니다. 차이는 **무조건 캐스팅하느냐, 조건부로 캐스팅하느냐**입니다.

|         | `std::move`                                          | `std::forward`                                           |
| ------- | ---------------------------------------------------- | -------------------------------------------------------- |
| 동작    | **무조건** rvalue로 캐스팅                           | 원래 값 범주(lvalue/rvalue)를 **그대로 복원**해서 캐스팅 |
| 인자    | 값 1개만 받음                                        | 값 + **템플릿 타입 `T`를 명시적으로 지정**해야 함        |
| 쓰는 곳 | 아무 데서나 (내가 이 값을 이제 버릴 거라는 걸 알 때) | forwarding reference(`T&&`)를 받은 템플릿 함수 내부      |
| 결과    | 항상 `T&&`                                           | 인자가 원래 lvalue였으면 `T&`, rvalue였으면 `T&&`        |

```cpp
std::string s = "hi";
std::move(s);        // 무조건 std::string&& 로 캐스팅 (s가 lvalue든 뭐든 상관없음)
std::forward<T>(s);   // T가 뭐냐에 따라 결과가 달라짐
```

### `std::forward`의 실제 구현

```cpp
template <class T>
constexpr T&& forward(remove_reference_t<T>& t) noexcept {
    return static_cast<T&&>(t);
}
```

핵심은 **매개변수 타입이 `T&`가 아니라 `remove_reference_t<T>&`** 라는 점입니다. `forward`는 인자로부터 `T`를 추론하지 않습니다. **호출하는 쪽에서 `T`를 직접 지정**해야 합니다 (`std::forward<T>(x)`).

`T&&`로 반환하는데도 결과가 상황에 따라 갈리는 이유는 바로 위에서 다룬 **참조 붕괴**가 여기서 그대로 작동하기 때문입니다.

- `T`가 `Foo&`(lvalue 전달됐던 경우)로 지정되면 → `T&& = Foo& &&` → 붕괴 → **`Foo&`** 반환 (여전히 lvalue)
- `T`가 `Foo`(rvalue 전달됐던 경우)로 지정되면 → `T&& = Foo&&` → **`Foo&&`** 반환 (rvalue)

즉 `forward`는 `move`처럼 무조건 `&&`를 강제하는 게 아니라, **템플릿 타입 추론 단계에서 이미 알아낸 원래 값 범주 정보를 `T`라는 형태로 저장해뒀다가, 그걸 이용해서 원래 성격 그대로 되살리는 것**입니다.

---

## 완벽한 전달(Perfect Forwarding)

### 문제 상황

어떤 템플릿 함수(래퍼)가 자신이 받은 인자를 그대로 다른 함수(내부 함수)에 넘기고 싶다고 가정해보겠습니다. 이때 원래 lvalue였던 건 lvalue로, rvalue였던 건 rvalue로 **성격을 그대로 유지한 채** 넘겨야 최적의 오버로드가 선택됩니다.

```cpp
void inner(Foo& x)  { std::cout << "lvalue 버전 호출\n"; }
void inner(Foo&& x) { std::cout << "rvalue 버전 호출\n"; }

// 문제가 있는 래퍼 - 매개변수에 이름이 붙는 순간 lvalue가 됨
template <class T>
void wrapper_bad(T&& x) {
    inner(x); // x는 이름이 있으니 항상 lvalue! → 무조건 inner(Foo&)만 호출됨
}

Foo f;
wrapper_bad(f);       // inner(Foo&) 호출 → 의도대로
wrapper_bad(Foo());    // Foo()는 rvalue인데도 inner(Foo&) 호출됨 → 의도와 다름! (이동 못 함)
```

`x`는 함수 본문에서 이름을 쓰는 순간 lvalue로 취급된다는 규칙 때문에, 원래 rvalue를 넘겼어도 그 정보가 래퍼 안에서 소실됩니다.

### 해결책: `std::forward<T>`

```cpp
template <class T>
void wrapper_good(T&& x) {
    inner(std::forward<T>(x)); // T를 알고 있으므로 원래 성격 복원 가능
}

wrapper_good(f);       // T = Foo&  → forward 결과 Foo&  → inner(Foo&)  호출 ✓
wrapper_good(Foo());    // T = Foo   → forward 결과 Foo&& → inner(Foo&&) 호출 ✓ (이동 가능!)
```

이렇게 **템플릿 함수가 자신이 받은 인자를 lvalue/rvalue 성격을 잃지 않고 다음 함수에 그대로 전달하는 기법**을 완벽한 전달(perfect forwarding)이라 부릅니다. 세 요소가 반드시 함께 있어야 성립합니다.

1. `T&&`(forwarding reference) 형태의 매개변수 — 반드시 템플릿 타입 매개변수 `T`에 직접 걸린 `&&`여야 함 (`vector<T>&&`처럼 T가 아닌 다른 타입에 붙은 `&&`는 그냥 rvalue reference일 뿐, forwarding reference가 아님)
2. 참조 붕괴 규칙 — `T`가 `T&`로 추론되냐 `T`로 추론되냐에 따라 정보가 인코딩됨
3. `std::forward<T>(x)` — 인코딩된 정보를 이용해 캐스팅 복원

### 실전 예시: `emplace_back`

`vector::emplace_back`이 완벽한 전달의 대표적인 실사용 예시입니다.

```cpp
template <class... Args>
void emplace_back(Args&&... args) {
    ::new (ptr) T(std::forward<Args>(args)...);
}

std::vector<std::string> v;
std::string s = "hello";

v.emplace_back(s);              // s는 lvalue → 복사 생성자 호출
v.emplace_back(std::move(s));    // move(s)는 rvalue → 이동 생성자 호출
v.emplace_back("literal");       // 임시 string 생성 → 이동 생성자 호출
```

`emplace_back`이 `std::forward`를 안 쓰고 그냥 `args`를 넘겼다면, `std::move(s)`로 넘긴 값도 함수 본문 안에서 이름을 갖는 순간 lvalue가 되어버려 항상 복사 생성자만 호출되는 비효율이 생겼을 겁니다.

---

## 결국 "move"는 어디서 결정되는가? — 컴파일러 vs 개발자

지금까지 다룬 여러 조각을 계층별로 다시 묶어보면, "move라는 메커니즘"은 **하나의 단일한 실체가 아니라 4개의 층위**로 이루어져 있습니다.

```
[1] 값 범주 판정 (lvalue/xvalue/prvalue)  →  100% 컴파일러 (언어 규칙)
        ↓
[2] T&& 타입과 오버로드 해석              →  100% 컴파일러 (언어가 지원하는 문법/메커니즘)
        ↓
[3] 이동 생성자/이동 대입 연산자의 내용    →  경우에 따라 다름 (아래 참고)
        ↓
[4] std::move 함수 자체                  →  100% 개발자가 짠 코드 (표준 라이브러리, 그냥 static_cast 래퍼)
```

**[1], [2]는 순수하게 컴파일러의 일**입니다. 어떤 표현식이 lvalue인지 rvalue인지 판정하는 것도, `T&&` 시그니처를 보고 오버로드 해석에서 어느 함수를 고를지 결정하는 것도 개발자가 관여할 수 없는 언어 규칙입니다.

**[4]는 순수하게 라이브러리 코드**입니다. `std::move`는 언어 기능이 아니라 `static_cast<T&&>(x)`를 감싼 평범한 템플릿 함수이고, 컴파일러의 특별한 처리 없이 누구나 똑같이 만들 수 있습니다.

**[3]이 가장 미묘한 지점**입니다. `T&&` 오버로드가 선택된 후 실제로 무엇을 하는지는 두 갈래로 나뉩니다.

- 멤버가 전부 단순한 타입(`int` 등)이라면 → **컴파일러가 이동 생성자를 암묵적으로 자동 생성**합니다 (멤버별로 재귀적으로 이동을 적용하는 방식).
- `vector`, `string`처럼 힙 자원을 소유하는 타입이라면 → 컴파일러는 "무엇이 자원인지, 어떻게 소유권을 넘겨야 하는지"를 알 수 없으므로, **표준 라이브러리 개발자(또는 그 클래스를 만든 사람)가 직접 소스코드로 작성**해야 합니다.

결론적으로 "rvalue를 구분하는 능력"은 컴파일러가 언어 차원에서 지원하는 메커니즘이고, `std::move`는 그 능력을 이용해 만든(개발자가 작성한) 아주 단순한 캐스팅 함수였습니다. 실제로 "무엇을 어떻게 옮길지"를 정의하는 이동 생성자는 단순한 타입이면 컴파일러가 자동 생성해주고, `vector`처럼 자원을 소유하는 타입이면 라이브러리 개발자가 직접 소스코드로 구현한 것입니다.