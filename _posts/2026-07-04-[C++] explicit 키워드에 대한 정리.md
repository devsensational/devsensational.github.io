---
title: "[C++] explicit 키워드에 대한 정리"
description: "explicit 키워드에 대해 정리했습니다"
date: 2026-07-04T09:52:50.952Z
tags: ["cpp"]
image:
  path: /assets/images/old/5cb169e4-12c1-44ea-9f88-0f0858be913d-image.png
categories: [CPP]
---
원문 출처
https://quuxplusone.github.io/blog/2023/04/08/most-ctors-should-be-explicit/


---
## 1. 컴파일러의 과도한 친절: 암시적 변환(Implicit Conversion)

C++ 컴파일러는 친절하게 설계된 부분들이 많습니다. 함수나 연산이 특정 타입의 객체를 요구할 때, 코더가 다른 타입을 넘겨주면 컴파일러는 에러를 내뿜기 전에 **어떻게든 객체를 변환해서 코드를 동작시키려고 시도**합니다.

문제는 이 친절함이 개발자의 의도와 다르게 작동할 때 발생합니다.

아래는 게임이나 서비스에서 특정 고유 ID를 가진 엔티티(Entity) 객체를 다룰 때 발생할 수 있는 문제의 예시입니다.

```cpp
class Player {
public:
    // 고유 ID를 받아서 플레이어 객체를 생성 (데이터베이스에서 불러온다고 가정)
    Player(int id) {
        cout << id << "번 유령 플레이어 임시 생성됨!\n";
    }
};

// 특정 플레이어에게 데미지를 입히는 함수
void attack(Player target) {
    cout << "타겟을 공격했습니다!\n";
}

int main() {
    int damageAmount = 50;
    
    // 개발자가 실수로 타겟 객체가 아닌 '데미지 수치'를 함수에 넣어버림
    attack(damageAmount); 
}
```

![](/assets/images/old/5cb169e4-12c1-44ea-9f88-0f0858be913d-image.png)

상식적으로 attack() 함수는 Player 객체를 요구하므로, 숫자 50을 넣으면 컴파일러가 타입이 맞지 않는다며 에러를 뱉어야 정상일 것입니다.

하지만 explicit이 없으면 컴파일러는 스스로 이렇게 생각합니다.
"어? Player를 달라고 했는데 숫자 50을 줬네? 잠깐, Player 클래스에 숫자를 받아서 객체를 만드는 생성자가 있잖아? 내가 알아서 Player(50)을 만들어서 넘겨줄게!"

결과적으로 에러는 나지 않고, 50번 아이디를 가진 유령 플레이어가 허공에 생성된 뒤 공격을 받게 됩니다. **의도와 맞지 않는 명령이 실행되면서, 나중에 원인을 찾기 위해 밤을 새우게 만드는 최악의 논리 버그가 됩니다.**

프로그램이 죽지는 않지만 이상하게 동작하는, 가장 디버깅하기 힘든 부류의 버그가 탄생하는 순간입니다.

만약, 생성자에 explicit Player(int id)를 붙였다면 애초에 attack(damageAmount)에서 컴파일 에러를 내주었을 것입니다.

## 2. explicit 키워드의 마법

생성자 앞에 `explicit`을 붙이면 컴파일러의 이런 자동 형변환을 금지할 수 있습니다. **"내가 명시적으로 객체를 생성한다고 적지 않는 한, 네 맘대로 변환하지 마!"**라고 컴파일러에게 선언하는 것입니다.

```cpp
class MyString {
public:
    explicit MyString(int size) { /* ... */ }
    // ...
};

printString(10); // ❌ 컴파일 에러 발생! (Cannot convert 'int' to 'MyString')

printString(MyString(10)); // ✅ 의도를 명확하게 밝혀야 통과됨

```

런타임에 발생할 논리적 버그를 **컴파일 타임 에러**로 끌어올려 즉각적으로 수정할 수 있게 해줍니다.

## 3. 실제 상황에서 발생할 수 있는 치명적인 문제 예시

`explicit`이 없을 때 발생한 사례를 찾아보았습니다.

### A. 예상치 못한 오버로딩 꼬임

https://www.reddit.com/r/cpp/comments/1hf4z7p/i_am_confused_as_to_when_to_use_explicit_in_a/?tl=ko

Reddit C++ 커뮤니티의 한 유저는 포인터가 암시적으로 `bool`로 변환되는 C++의 특성 때문에 버그를 겪은 사례를 공유했습니다.

예시로 어떤 함수 `Foo(bool)`과 `Foo(MyClass)`가 있을 때, 포인터를 넘겼더니 의도치 않게 `bool` 관련 로직이나 엉뚱한 암시적 생성자를 타고 들어가는 식의 오버로딩 꼬임 현상이 발생하였다고 합니다. 

`explicit`은 타입 간의 조용한 변환을 막아 오버로딩 모호성을 줄이므로 이런 문제를 예방할 수 있습니다.

### B. 숨겨진 성능 저하 (Hidden Performance Costs)

객체를 생성하는 데 비용이 많이 드는(Heavy) 클래스라면 암시적 변환은 치명적인 성능 저하를 유발합니다.

```cpp
void processData(const BigDataContainer& data);

// 만약 BigDataContainer(int id)가 explicit이 아니라면?
processData(1004); // int 하나만 넘겼는데 뒤에서 수십 MB 메모리 할당이 일어날 수 있음

```

`explicit`을 사용하면 사용자가 `processData(BigDataContainer(1004))`처럼 명시적으로 코드를 작성해야 하므로, **무거운 객체가 여기서 생성 된다**라는 것을 인지할 수 있게 됩니다.

### C. C++11 이후: 다중 인자와 중괄호 초기화의 함정

과거에는 "인자가 1개인 생성자"만 조심하면 됐지만, C++11의 중괄호 초기화(Braced Initialization)가 도입되면서 다중 인자 생성자에서도 암시적 변환이 일어납니다.

```cpp
struct Rectangle {
    Rectangle(int width, int height) {}
};
void draw(Rectangle r);

draw({10, 20}); // 암시적 변환 허용. 

```

편리해 보이지만, 코드가 복잡해질수록 `{10, 20}`이 무엇을 의미하는지 문맥상 파악하기 힘들어집니다. 생성자를 `explicit Rectangle(int, int)`로 만들면 `draw(Rectangle{10, 20})`으로 작성하도록 강제할 수 있어 코드의 가독성과 안전성이 높아집니다.

### D. 배열 크기와 데이터 값의 혼동

```cpp
#include <iostream>

class IntArray {
public:
    // 숫자를 하나 받아서 "그 숫자만큼의 크기"를 가진 빈 배열을 만듦
    IntArray(int size) {
        cout << "크기가 " << size << "인 빈 배열 생성\n";
    }
};

// 학생들의 시험 점수 배열을 받아서 평균을 계산하는 함수
void calculateAverage(const IntArray& scores) {
    // ... 평균 계산 로직 ...
}

int main() {
    int myScore = 95;
    
    // 개발자의 의도: "내 점수(95) 하나만 일단 넣어서 계산해볼까?"
    calculateAverage(myScore); 
}
```
![](/assets/images/old/3f91d62e-56b2-4eae-b222-5ab12fd0764e-image.png)

개발자는 95점이라는 **int형 데이터** 하나를 전달하고 싶었습니다. 하지만 컴파일러는 또다시 친절함을 발휘해 IntArray(95)를 호출해 버립니다.

결과적으로 95점이라는 데이터가 전달된 것이 아니라, 크기가 95칸인 텅 빈 0점짜리 배열이 함수로 넘어가게 됩니다. 프로그램은 죽지 않고 평균 0점이라는 엉뚱한 결과를 출력하게 됩니다.

## 4. explicit 사용의 골든 룰 (언제 쓰고, 언제 생략할까?)

Arthur O'Dwyer는 "몇 가지 예외를 제외한 99%의 생성자에는 explicit을 붙이는 것이 옳다"고 강조합니다. C++의 기본값은 암시적 변환 허용이지만, 이는 과거 C언어와의 호환성 때문이며 현대적인 소프트웨어 공학 관점에서는 모든 생성자에 `explicit`을 기본으로 다는 것이 좋습니다.

하지만 **반드시 `explicit`을 생략해야 하는 예외 상황**들도 있습니다.

1. **복사 및 이동 생성자**
`MyClass(const MyClass&)` 같은 복사 생성자를 명시적으로 만들면 `MyClass a = b;` 와 같은 기본적인 대입조차 막히게 되므로 절대 붙여서는 안 됩니다.
2. **`std::initializer_list`를 받는 생성자**
`std::vector<int> v = {1, 2, 3};` 처럼 배열 형태로 값을 집어넣어 초기화하는 컨테이너 타입들은 암시적 변환이 그 자체의 목적이므로 생략해야 합니다.
3. **단순 데이터 묶음 (C-Struct 대체품)**
`std::pair`나 `std::tuple`처럼 순수하게 데이터를 담는 바구니 역할만 하는 구조체라면 중괄호 `{}`를 통한 암시적 변환을 허용하는 것이 자연스럽습니다.
4. **본질적으로 같은 데이터를 표현하는 경우**
`const char*`에서 `std::string`으로 변환되거나, `int`에서 직접 만든 `BigInt` 클래스로 변환되는 것처럼 "의미론적으로 완전히 동일한 개념"일 때는 묵시적 변환이 편리합니다.

---

### 💡 `operator bool`에도 explicit을 붙이세요!

생성자 외에도 `explicit`이 빛을 발하는 곳이 바로 형변환 연산자입니다. 객체가 유효한지 검사하기 위해 `operator bool`을 정의하는 경우가 많습니다.

```cpp
class SmartPtr {
public:
    explicit operator bool() const { return ptr != nullptr; }
    // ...
};

```

여기에 `explicit`을 붙이면 `if (myPtr)` 같이 조건문 안에서는 정상적으로 작동(Contextual conversion)하지만, `int x = myPtr + 1;` 처럼 포인터가 실수로 숫자로 변환되어 연산되는 대참사는 컴파일러가 막아줍니다. 아래는 예시 코드를 실제 IDE에 적용한 것입니다.

#### explicit 키워드 사용 전
![](/assets/images/old/ec1ceb72-9049-4e53-bf04-776860a40349-image.png)

#### explicit 키워드 사용 후
![](/assets/images/old/7480a37d-fe81-4d32-9cf8-34fecf8c88fd-image.png)


---

명확한 이유가 없다면 **작성하는 모든 생성자(심지어 파라미터가 없는 기본 생성자 포함)에 일단 `explicit`을 붙이는 습관**을 들이는 것이 더 안전한 C++ 코드를 작성하는 지름길이라는 것을 깨달았습니다.