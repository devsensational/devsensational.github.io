---
title: "[C++/CS] Deadlock 문제"
description: "데드락(Deadlock)은 두 개 이상의 프로세스나 스레드가 서로가 보유한 자원을 기다리면서 영원히 대기 상태에 빠지는 문제를 의미합니다. 즉, 서로가 서로를 기다리기 때문에 아무도 앞으로 진행하지 못하는 상태라고 볼 수 있습니다."
date: 2025-11-18T11:29:13.615Z
tags: ["computer science","c++"]
image:
  path: /assets/images/old/4bcffb8e-8047-44ff-a8e1-6db481a46fb4-image.png
categories: [C++]
---
데드락(Deadlock)은 두 개 이상의 프로세스나 스레드가 서로가 보유한 자원을 기다리면서 **영원히 대기 상태에 빠지는 문제**를 의미합니다. 즉, **서로가 서로를 기다리기 때문에 아무도 앞으로 진행하지 못하는 상태**라고 볼 수 있습니다. 

멀티 스레드 환경에서 자원 잠금을 잘못 처리하면 쉽게 발생할 수 있는 대표적인 동시성 문제입니다.

---

## 데드락이 발생하기 위한 4가지 조건 (Coffman 조건)

데드락은 아래 4가지 조건이 모두 만족해야 발생합니다.

1. **상호 배제(Mutual Exclusion)**

   * 자원을 동시에 사용할 수 없습니다. (예: mutex)

2. **점유와 대기(Hold and Wait)**

   * 이미 자원을 보유한 상태에서 다른 자원을 기다립니다.

3. **비선점(No Preemption)**

   * 다른 프로세스가 보유한 자원을 강제로 빼앗을 수 없습니다.

4. **순환 대기(Circular Wait)**

   * 여러 프로세스가 서로가 보유한 자원을 기다리는 순환 구조가 형성됩니다.


이 중 **하나라도 깨면 데드락을 방지할 수 있습니다.** (중요)

---

## 데드락 예시: 두 개의 Mutex 잠금 순서 충돌

아래 예시는 데드락이 실제로 발생하는 C++ 코드입니다.
ThreadA와 ThreadB가 서로 반대로 mutex를 잠금으로써 데드락이 발생합니다.


```cpp
#include <iostream>
#include <thread>
#include <mutex>
#include <chrono>

using namespace std;

mutex m1;
mutex m2;

void ThreadA() {
    cout << "[ThreadA] Lock m1\n";
    m1.lock();
    this_thread::sleep_for(chrono::milliseconds(100));

    cout << "[ThreadA] Try Lock m2\n";
    m2.lock();  // ThreadB가 m2를 잡고 있으므로 데드락
}

void ThreadB() {
    cout << "[ThreadB] Lock m2\n";
    m2.lock();
    this_thread::sleep_for(chrono::milliseconds(100));

    cout << "[ThreadB] Try Lock m1\n";
    m1.lock();  // ThreadA가 m1을 잡고 있으므로 데드락
}

int main() {
    thread t1(ThreadA);
    thread t2(ThreadB);

    t1.join();
    t2.join();

    return 0;
}
```

### 실행결과
![](/assets/images/old/4bcffb8e-8047-44ff-a8e1-6db481a46fb4-image.png)

이 상태에서 프로그램이 더 이상 진행되지 않았습니다.


---

## 데드락을 예방하는 방법

### 1) 자원 획득 순서를 통일하기

모든 스레드가 **항상 같은 순서(A → B)**로 자원을 잠그도록 합니다.
이렇게 하면 순환 대기 조건을 깨뜨릴 수 있습니다.
=> AB/BA 금지

### 2) `std::scoped_lock` 사용하기 (C++17 이상)

```cpp
std::scoped_lock lock(m1, m2);
```

두 mutex를 데드락 없이 안전하게 한 번에 잠글 수 있습니다.

### 3) 타임아웃 기반 `try_lock` 사용

자원을 못 획득하면 아예 포기하거나 재시도하여 무한 대기를 피합니다.

