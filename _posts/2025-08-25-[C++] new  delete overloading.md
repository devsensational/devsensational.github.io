---
title: "[C++] new / delete overloading"
description: "C++에서 객체를 동적으로 생성할 때 흔히 new와 delete 연산자를 사용합니다. 표면적으로는 malloc/free와 비슷해 보이지만, 실제 내부 동작은 훨씬 더 복잡하고 강력합니다."
date: 2025-08-25T10:24:12.155Z
tags: ["C++","메모리"]
categories: [C++]
---
C++에서 객체를 동적으로 생성할 때 흔히 new와 delete 연산자를 사용합니다. 표면적으로는 malloc/free와 비슷해 보이지만, 실제 내부 동작은 훨씬 더 복잡하고 강력합니다.

이번 포스트에서는 new와 delete가 내부적으로 어떻게 동작하는지 왜, 어떻게 오버로딩할 수 있는지 정리하려고 합니다.

# new와 delete의 원리
## new의 동작 과정

new는 단순히 메모리만 확보하는 것이 아닙니다. 두 단계로 이루어집니다.

**1. 메모리 확보 (allocation)**
* 전역 ::operator new(size_t)가 호출됩니다.
 * 기본 구현은 malloc(size)와 유사하며, 실패 시 std::bad_alloc 예외를 던집니다.
   
**2. 객체 생성 (construction)**
*  확보한 메모리 주소에 객체의 **생성자(Constructor)**를 호출합니다.
* 내부적으로는 placement new(new(ptr) Type(...))가 사용됩니다.

즉, 다음 코드:

```cpp
MyClass* obj = new MyClass(10);
```

은 내부적으로 대략 이렇게 작동합니다:

```cpp
void* raw = ::operator new(sizeof(MyClass));   // 메모리 확보
try {
    obj = static_cast<MyClass*>(raw);
    new (obj) MyClass(10);  // placement new로 생성자 호출
} catch (...) {
    ::operator delete(raw); // 생성자에서 예외 발생 시 메모리 해제
    throw;
}
```

## delete의 동작 과정

delete 역시 두 단계로 이루어집니다.

**1. 객체 소멸 (destruction)**
- 해당 포인터가 가리키는 객체의 **소멸자(Destructor)**를 호출합니다.

**2. 메모리 해제 (deallocation)**
- 전역 ::operator delete(void*)가 호출됩니다.
- 기본 구현은 free(ptr)와 유사합니다.

예시:
``` cpp
delete obj;
```

은 내부적으로 이렇게 동작합니다:
```cpp
if (obj != nullptr) {
    obj->~MyClass();        // 소멸자 호출
    ::operator delete(obj); // 메모리 해제
}
```

# new / delete 오버로딩

C++에서는 전역 단위 또는 클래스 단위에서 new와 delete를 오버로딩할 수 있습니다.
이때 오버로딩되는 것은 메모리 확보/해제 부분이지, 생성자와 소멸자 호출 과정은 그대로 유지됩니다.

## 전역 오버로딩
```cpp
void* operator new(size_t size) {
    cout << "[Global new] size: " << size << endl;
    return malloc(size);
}

void operator delete(void* ptr) noexcept {
    cout << "[Global delete]" << endl;
    free(ptr);
}
```


-  프로그램 전체에서 new/delete 호출 시 위 구현이 사용됩니다.
- 주로 메모리 추적, 디버깅, 커스텀 로거 등에 활용합니다.

## 클래스 단위 오버로딩
```cpp
class MyClass {
public:
    void* operator new(size_t size) {
        cout << "[MyClass new] size: " << size << endl;
        return ::operator new(size); // 전역 new 호출
    }

    void operator delete(void* ptr) {
        cout << "[MyClass delete]" << endl;
        ::operator delete(ptr); // 전역 delete 호출
    }
};

int main() {
    MyClass* obj = new MyClass();  // MyClass::operator new 호출
    delete obj;                    // MyClass::operator delete 호출
}
```

-  해당 클래스 객체에 대해서만 오버로딩된 new/delete가 동작합니다.
-  특정 클래스의 메모리 풀 관리에 유용합니다.

## 언제 유용할까요?
>
**메모리 풀(Pool) 관리**: 빈번한 객체 생성/삭제 성능 최적화
**로깅/디버깅: 누수 추적,** 메모리 사용량 측정
**특수 메모리 영역 관리**: 공유 메모리, GPU 메모리 등

## 주의할 점
- ```operator new```는 생성자 호출을 포함하지 않는다.
- ```operator delete```는 소멸자 호출을 포함하지 않는다.
- 따라서 오버로딩 시 ```::operator new``` / ```::operator delete```를 적절히 호출해줘야 한다.
- **placement new**와는 다르다 → placement new는 이미 확보된 메모리에 객체를 생성하는 역할만 한다.

# 정리
- ```new``` = 메모리 할당 + 생성자 호출
- ```delete``` = 소멸자 호출 + 메모리 해제
- 오버로딩하면 할당/해제 부분만 커스터마이징 가능
- 주로 성능 최적화, 디버깅, 특수 메모리 관리에 활용