---
title: "[C++] iterator, reverse_iterator의 차이점"
description: "iterator, reverse_iterator의 차이점에 대해 알아봤습니다"
date: 2026-07-26T09:29:10.269Z
tags: ["C++"]
image:
  path: /assets/images/old/0b2670e3-e473-479f-88a7-d1b4729f633f-image.png
categories: [C++]
---
### 라이선스 표기

>
Copyright (c) Microsoft Corporation.
SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
모든 코드는 표기된 라이센스를 따르며, 설명을 위해 수정된 사항이 있습니다

### 원문 출처
>
https://github.com/microsoft/STL/blob/main/stl/inc/iterator
https://github.com/microsoft/STL/blob/main/stl/inc/xutility
https://learn.microsoft.com/ko-kr/cpp/standard-library/reverse-iterator-class?view=msvc-170
https://learn.microsoft.com/ko-kr/cpp/standard-library/iterator?view=msvc-170
https://en.cppreference.com/cpp/iterator/reverse_iterator

---
![](/assets/images/old/0b2670e3-e473-479f-88a7-d1b4729f633f-image.png)

STL vector에서 `rbegin()`으로 리턴받은 iterator를 인자로 사용하여 `erase()`를 시도했지만 타입이 맞지 않는다는 에러가 발생했습니다. 

`begin()`은 ` vector<T>::iterator`을 반환하고 `rbegin()`은 `vector<T>::reverse_iterator`를 반환하고 있었습니다. 또한, 연산 방향이나 종료 지점에도 차이가 존재했습니다.


| **구분** | **begin()** | **rbegin()** |
| --- | --- | --- |
| **의미** | Begin (시작) | **Reverse** Begin (역방향 시작) |
| **시작 위치** | 첫 번째 요소 (`[0]`) | 마지막 요소 (`[N-1]`) |
| **종료 지점** | `end()` (마지막 다음 칸) | `rend()` (첫 번째 이전 칸) |
| **`++` 연산 시** | 오른쪽으로 이동 | 왼쪽으로 이동 |


---

### 그럼 `reverse_iterator`로 `erase()`를 실행하려면 어떻게 해야할까요?

먼저 `reverse_iterator`에 대해 알아봤습니다.

https://github.com/microsoft/STL/blob/main/stl/inc/xutility

![](/assets/images/old/d3e212ff-d945-4eb9-9c0f-b4c7fa49201c-image.png)


`reverse_iterator`는 기본적으로 사용하던 양방향 반복자(Bidirectional Iterator, BidIt)를 기본적으로 가지고 있으며, 이를 랩핑하여 구현하고 있습니다.

```cpp
_NODISCARD _CONSTEXPR17 _BidIt base() const noexcept(...) {
    return current; // 내부에 들고 있던 원본 iterator를 그대로 반환
}
```

`base()`는 이 `current(기존 iterator)`를 그대로 반환합니다. 

그럼 `rit.base()`를 사용하면 `erase()`를 정상적으로 호출할 수 있을까요? 호출은 할 수 있지만 의도와는 다르게 작동합니다. **`*rit`은 `current`에서 왼쪽 주소를 역참조할 뿐, 실제 물리적 주소는 의도와 다르기 때문입니다.** 

![](/assets/images/old/65d2e9fc-506a-4161-a0b9-5d910072847e-image.png)

```cpp
_NODISCARD _CONSTEXPR17 reference operator*() const noexcept(...) {
    _BidIt _Tmp = current; // 현재 들고 있는 iterator(current)를 복사
    return *--_Tmp;        // 복사본을 1칸 앞으로(--) 이동시킨 후 역참조(*)해서 반환
}
```

**따라서, 역참조한 주소의 데이터를 지우고 싶다면 전후에 값을 왼쪽으로 옮겨줘야 합니다.**


### 소스코드 및 결과

```cpp
int main() {
    vector<int> v = { 10, 20, 30, 40, 50 };

    // 역방향 순회 중 '30'을 삭제하고 싶은 경우
    for (auto rit = v.rbegin(); rit != v.rend(); ) {
        if (*rit == 30) {
            cout << "반복자를 이동시키지 않았을 때, 반환되는 역참조 값: " << *rit.base() << '\n';

            // rit.base()는 30이 아닌 '40'의 위치를 가리키고 있음
            // 따라서 next(rit).base()를 전달해야 정확히 '30' 위치의 iterator가 됨
            auto it = std::next(rit).base();

            // erase는 삭제 후 다음 위치의 정방향 iterator를 반환하므로,
            // 이를 다시 reverse_iterator로 감싸서 갱신
            rit = vector<int>::reverse_iterator(v.erase(it));
        }
        else {
            ++rit;
        }
    }

    // 결과 출력: 10 20 40 50
    for (int n : v) cout << n << " ";
}
```
![](/assets/images/old/25ddd1d1-ef56-4db5-9e74-9662b3eaba2b-image.png)

