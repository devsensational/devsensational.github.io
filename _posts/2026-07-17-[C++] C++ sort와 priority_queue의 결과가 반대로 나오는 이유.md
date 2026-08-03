---
title: "[C++] C++ sort와 priority_queue의 결과가 반대로 나오는 이유"
description: "C++에서 sort()와 priority_queue는 동일한 비교 함수를 사용할 때, 결과가 반대로 나오는 것처럼 보이는 이유가 무엇인지 분석했습니다."
date: 2026-07-17T07:23:22.585Z
tags: ["c++"]
categories: [C++]
---

### 원문 출처
[cppreference.com - priority_queue](https://en.cppreference.com/w/cpp/container/priority_queue)
[cppreference.com - make_heap](https://en.cppreference.com/w/cpp/algorithm/make_heap)
[cppreference.com - Compare](https://en.cppreference.com/w/cpp/named_req/Compare)

### 라이선스 표기
>
**Copyright (c) Microsoft Corporation.
SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
모든 코드는 표기된 라이센스를 따르며, 설명을 위해 수정된 사항이 있습니다**


---

C++ 코테와 개발을 하다 갑자기 궁금한 점이 생겼습니다. `sort`와 `priority_queue`에 동일한 비교 함수(예: `greater<int>`)를 넘겨주었는데, **출력되는 데이터의 정렬 순서가 정반대**로 나오는 현상입니다.

>
*   `sort(..., std::greater<int>())` $\\rightarrow$ **내림차순** (큰 값부터)
*   `priority_queue<int, vector<int>, greater<int>>` $\\rightarrow$ **오름차순** (작은 값부터 차례대로 `top()`)

동일한 비교 함수(예: `less<>` 또는 `a < b`)를 전달했을 때 결과가 반대로 나오는 핵심 이유는 두 자료구조가 비교 함수의 결과를 해석하고 활용하는 목적이 정반대이기 때문입니다.

`sort()`는 배열을 선형적으로 정렬하기 위해 비교 함수를 '선행 조건'으로 사용하는 반면, `priority_queue`는 트리(Heap)의 루트에 최댓값을 올리기 위해 비교 함수를 '우선순위 역전 조건'으로 사용합니다.

#### 1. `sort`의 선형 정렬과 엄격한 약한 순서(Strict Weak Ordering)

`sort`는 컨테이너의 요소들을 선형적으로 정렬합니다. C++의 모든 정렬 알고리즘은 **엄격한 약한 순서(Strict Weak Ordering)** 라는 수학적 규칙을 기반으로 동작합니다.


> Strict Weak Ordering에 대해 요약한 블로그 글
https://hanarotg.tistory.com/224

`sort`에 전달된 비교 함수 `comp(a, b)`가 `true`를 반환한다는 것은 "정렬된 결과에서 a가 b보다 무조건 앞에 위치해야 한다"는 것을 의미합니다.

>
* **`less<T>` 적용 시:** 내부적으로 `a < b`를 평가합니다. 이 값이 `true`라면 더 작은 요소가 앞에 배치되므로 최종적으로 **오름차순** 정렬이 됩니다.
* **`greater<T>` 적용 시:** 내부적으로 `a > b`를 평가합니다. 더 큰 요소가 앞에 배치되어야 하므로 최종적으로 **내림차순** 정렬이 됩니다.

즉, `sort`에서 비교 연산자는 **요소들의 최종적인 선형 배치 순서 그 자체**를 결정합니다.


#### 2. priority_queue의 힙(Heap) 구성 원리

반면 `priority_queue`는 내부적으로 트리 기반의 힙(Heap) 자료구조를 유지하기 위해 비교 연산자를 사용합니다. 컨테이너 어댑터인 `priority_queue`는 요소 삽입과 삭제 시 내부적으로 `<algorithm>` 헤더의 `push_heap`과 `pop_heap` 알고리즘을 호출합니다.

힙을 구성할 때 C++ 표준 알고리즘은 부모 노드와 자식 노드를 비교합니다. 이때 비교 함수 `comp(parent, child)`가 `true`를 반환하면, **부모 노드가 자식 노드보다 우선순위가 낮다고 판단하여 두 노드의 위치를 교환(Swap)** 합니다. 즉, 자식 노드를 부모 위치로 끌어올립니다.

>
* **`less<T>` 적용 시:** `parent < child`가 `true`일 때 위치를 바꿉니다. 작은 값이 아래로 내려가고 큰 값이 루트 노드(Top)로 올라가게 됩니다. 그 결과, 가장 큰 값이 최상단에 위치하는 **최대 힙(Max-Heap)** 이 형성됩니다.
* **`greater<T>` 적용 시:** `parent > child`가 `true`일 때 위치를 바꿉니다. 큰 값이 아래로 내려가고 작은 값이 루트 노드로 올라갑니다. 결과적으로 가장 작은 값이 최상단에 위치하는 **최소 힙(Min-Heap)** 이 형성됩니다.

---

### sort()가 힙 정렬을 사용하게 되면 priority_queue와는 어떤 차이가 있을까요?
`sort()`는 최악의 상황에서도 $O(N \log N)$의 시간 복잡도를 보장하면서, 평균적인 성능을 극대화하기 위해 **하이브리드 정렬 알고리즘**을 사용합니다. 퀵, 힙, 삽입 정렬을 기준에 따라 사용하게 되는데, 퀵 정렬을 사용하다가 재귀 깊이가 임계점을 초과하면 힙 정렬로 즉시 전환하게 됩니다.

```cpp

//sort()
//<algorithm>
template <class _RanIt, class _Pr>
_CONSTEXPR20 void _Sort_unchecked(_RanIt _First, _RanIt _Last, _Iter_diff_t<_RanIt> _Ideal, _Pr _Pred) {
    // order [_First, _Last)
    for (;;) {
        if (_Last - _First <= _ISORT_MAX) { // small
            _STD _Insertion_sort_unchecked(_First, _Last, _Pred);
            return;
        }

        // 💡 [분기점] 재귀 깊이 임계값을 초과했을 때 (힙 정렬로 전환)
        // 피벗이 한쪽으로 계속 치우쳐서 퀵 정렬이 최악의 시간복잡도 O(N^2)로 향하고 있다면,
        // 허용된 분할 횟수(_Ideal)가 0 이하가 됩니다. 
        // 이때 즉시 '최소 힙'을 만들고 뒤집어서 강제로 정렬을 마칩니다.
        if (_Ideal <= 0) { // heap sort if too many divisions
            _STD _Make_heap_unchecked(_First, _Last, _Pred); // 1단계: 힙 생성[cite: 1]
            _STD _Sort_heap_unchecked(_First, _Last, _Pred); // 2단계: 뒤에서부터 재배치[cite: 1]
            return;
        }
        
        auto _Mid = _STD _Partition_by_median_guess_unchecked(_First, _Last, _Pred);
        
        _Ideal = (_Ideal >> 1) + (_Ideal >> 2); // allow 1.5 log2(N) divisions

        
        if (_Mid.first - _First < _Last - _Mid.second) { 
            _STD _Sort_unchecked(_First, _Mid.first, _Ideal, _Pred);
            _First = _Mid.second; // 다음 루프에서는 우측 영역을 대상으로 시작
        } else { 
            _STD _Sort_unchecked(_Mid.second, _Last, _Ideal, _Pred);
            _Last = _Mid.first; // 다음 루프에서는 좌측 영역을 대상으로 시작
        }
    }
}
```

이때, 힙을 생성하는 과정은 `priority_queue`와 같은 방법을 사용합니다. (__msvc_heap_algorithm.hpp)

```cpp
//priority_queue
//<queue>
void _Make_heap() {
    _STD make_heap(c.begin(), c.end(), _STD _Pass_fn(comp));
}

// __msvc_heap_algorithms.hpp
_EXPORT_STD template <class _RanIt, class _Pr>
_CONSTEXPR20 void make_heap(_RanIt _First, _RanIt _Last, _Pr _Pred) { // make [_First, _Last) into a heap
    _STD _Adl_verify_range(_First, _Last);
    
    // ★ 같은 함수를 사용하는 지점
    _STD _Make_heap_unchecked(_STD _Get_unwrapped(_First), _STD _Get_unwrapped(_Last), _STD _Pass_fn(_Pred));
}

//sort()
//<algorithm>
_CONSTEXPR20 void _Sort_unchecked(_RanIt _First, _RanIt _Last, _Iter_diff_t<_RanIt> _Ideal, _Pr _Pred) {
(...)
if (_Ideal <= 0) { // heap sort if too many divisions
			// ★ 같은 함수를 사용하는 지점
            _STD _Make_heap_unchecked(_First, _Last, _Pred); // 1단계: 힙 생성[cite: 1]
            _STD _Sort_heap_unchecked(_First, _Last, _Pred); // 2단계: 뒤에서부터 재배치[cite: 1]
            return;
        }
(...)
}
```

순서가 뒤집히는 분기점은 `_Sort_heap_unchecked`였습니다. 정렬이 완료된 후, 힙에 쌓인 데이터를 배열에 재배치할 때 차이가 발생합니다.
```cpp
template <class _RanIt, class _Pr>
_CONSTEXPR20 void _Sort_heap_unchecked(_RanIt _First, _RanIt _Last, _Pr _Pred) {
    // 힙 구조가 완성된 상태에서 맨 마지막 원소(_Last - 1)부터 역방향으로 진행합니다.
    for (; 2 <= _Last - _First; --_Last) {
        
        // 핵심 분기점: 루트 노드(_First)에 있는 최우선순위 값을 
        // 배열의 맨 마지막 칸(_Last - 1)으로 이동시키고 영역을 1칸 줄입니다.
        _STD _Pop_heap_unchecked(_First, _Last, _Pred);
    }
}
```

이 루프가 작동하는 과정은 다음과 같습니다.

>
**첫 번째 루프:** 현재 최소 힙의 루트(0번 칸)에 있는 가장 작은 값을 뽑아내어 배열의 맨 마지막 칸에 채워 넣습니다.
**두 번째 루프:** 남은 원소들로 다시 최소 힙을 구성하면 루트에 두 번째로 작은 값이 올라옵니다. 이 값을 다시 배열의 뒤에서 두 번째 칸에 채워 넣습니다.
**반복 결과:** 가장 작은 값들이 배열의 뒤쪽 공간부터 역순으로 차곡차곡 쌓이게 됩니다.

최종적으로 배열의 앞쪽에는 큰 값들이 남고, 배열의 맨 뒤에 가장 작은 값이 배치되므로 전체 배열을 출력했을 때 내림차순의 형태를 띠게 되는 것입니다.

결국 동일한 기준(e.g. comp 함수로 `greater<>`를 사용)을 적용하더라도 결과가 반대인 이유는 인출 및 저장 메커니즘의 차이 때문이었습니다.