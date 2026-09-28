---
title: C++ vector의 재할당과 Dangling Pointer
date: 2026-09-28 12:35 +0900
category: [CPP]
tags: [cpp]
description: 재할당 전에 얻어 둔 element의 포인터/참조/반복자는 옛 주소를 그대로 들고 있음
image:
  path: /assets/images/2026-09-28/3.png
math: true
---

## 개요

- `std::vector`는 요소를 항상 하나의 연속된 메모리에 두어야 함
- 공간이 부족하면 더 큰 버퍼를 새로 잡고 element를 통째로 옮긴 뒤 옛 버퍼를 해제 하며, 이를 재할당(reallocation)이라고 함
- 재할당 전에 얻어 둔 요소의 포인터/참조/반복자는 옛 주소를 그대로 들고 있음
- 옛 버퍼가 해제되는 순간 이들은 반환된 메모리를 가리키는 댕글링 포인터가 됨

## 재할당 수행 순서

`size() == capacity()`인 상태에서 `push_back`을 호출하면 다음 순서로 진행됨.

1. **용량 부족 판단**: 빈자리가 없으므로 재할당 수행
2. **새 capacity 계산**: 기존 capacity의 배수로 키움. 이 덕분에 `push_back`은 평균적으로 O(1)
3. **새 버퍼 할당**: allocator로 더 큰 연속 메모리를 받음. 실패하면 `std::bad_alloc`이 던져지고 기존 벡터는 그대로 남음
4. **새 요소를 먼저 생성**: 추가할 요소를 새 버퍼의 끝자리에 먼저 만든다. 옛 버퍼가 살아 있는 동안 복사가 끝나므로 `v.push_back(v[0])`도 안전함
5. **기존 요소 이동**: `std::move_if_noexcept`규칙을 따름
   1. 이동 생성자가 `noexcept`면 이동함
   2. 아니면 복사함. 이동 중 예외가 발생하면 원본이 발생할 수 있기 때문
   3. 도중에 예외가 나면 새 버퍼를 정리하고 원래 상태로 되돌림(strong exceptino guarantee)
6. **옛 요소 소멸**: 옛 버퍼에 남은 요소들의 소멸자를 호출
7. **옛 버퍼 해제**: 옛 메모리를 반환함. 이 시점에서 옛 주솔르 가리키던 포인터는 모두 댕글링임
8. **내부 포인터 갱신**: 벡터의 시작/끝/용량 포인터를 새 버퍼 기준으로 바꿈. 이후 data(), begin()은 새 주소를 돌려줌

### 재할당 발생 관찰 코드

```cpp
vector<int> v;
const int* prev = nullptr;
for (int i = 0; i < 20; ++i) {
    v.push_back(i);
    if (v.data() != prev) {
        cout << "재할당: capacity=" << v.capacity()
                  << ", 새 주소=" << v.data() << '\n';
        prev = v.data();
    }
}
```

![](/assets/images/2026-09-28/1.png)

## MSVC STL code

- 재할당 시 바뀌는 것은 `vector` 오브젝트의 주소가 아니라, 오브젝트 안에 든 포인터 3개(`_Myfirst`, `_Mylast`, `_Myend`)임
- MSVC STL에서 이 값을 새 버퍼로 바꾸는 곳은 `_Change_array`

[https://github.com/microsoft/STL/blob/main/stl/inc/vector](https://github.com/microsoft/STL/blob/main/stl/inc/vector)

### 호출 경로

![](/assets/images/2026-09-28/2.png)

- 삽입이든 `reserve`든 새 버퍼가 필요한 경로는 모두 `_Change_array`로 모임

### 포인터 재설정 코드

```cpp
// _Myfirst, _Mylast, _Myend는 _Mypair._Myval2 멤버에 대한 참조(pointer&)
_My_data._Orphan_all();

if (_Myfirst) { // destroy and deallocate old array
    _STD _Destroy_range(_Myfirst, _Mylast, _Al);
    // ...
    _Al.deallocate(_Myfirst, static_cast<size_type>(_Myend - _Myfirst));
}

_Myfirst = _Newvec;
_Mylast  = _Newvec + static_cast<_Iter_diff_t<pointer>>(_Newsize);
_Myend   = _Newvec + static_cast<_Iter_diff_t<pointer>>(_Newcapacity);
```

1. `_Orphan_all()`: 디버그 빌드에서 컨테이너에 등록된 반복자를 모두 떼어냄
2. `_Destory_range`: 옛 버퍼에 남은 요소의 소멸자를 호출함
3. deallocate: 옛 버퍼를 반환한다. 이 줄이 실행되는 순간 옛 주소를 들고 있던 외부 포인터가 댕글링이 됨
4. 세 포인터 대입: `_Myfirst`, `_Mylast`, `_Myend`가 참조이므로 vector 오브젝트의 멤버가 제자리에서 새 버퍼 기준으로 바뀜

- `vector`오브젝트 자체는 옮겨지지 않고 멤버 값만 덮어 쓰므로, `vector<int>* pv = &v;`처럼 `vector` 오브젝트를 가리키는 포인터는 재할당 뒤에도 유효함
- 반면 `_Myfirst`의 옛 값을 복사해 둔 반복자는 모두 옛 버퍼를 가리킴
- `_Change_array`는 `noexcept`라서 여기서는 예외가 나지 않고, 실패할 수 있는 일은 모두 2단계에서 끝남

## 재할당 시 포인터가 댕글링이 되는 과정

- 핵심은 외부 포인터 `p`의 값이 재할당 중에도 바뀌지 않는다는 점
- `vector`는 자기 내부 포인터만 갱신할 뿐, 밖에서 요소 주소를 들고 있는 포인터가 있는지 알 방법이 없음
  
![](/assets/images/2026-09-28/3.png)

1. **재할당 전**: int* p = &v[0];으로 옛 버퍼의 첫 요소 주소를 저장한다. 이때는 유효함
2. **요소 이동**: 새 버퍼가 할당되고 요소가 옮겨진다. p는 여전히 옛 주소를 가리키지만, 옛 버퍼가 아직 해제되지 않아 접근은 가능함
3. **옛 버퍼 해제**: 옛 메모리가 반환되면 p는 해제된 메모리를 가리킨다. *p 접근은 UB다. 크래시가 나거나, 쓰레기 값을 읽거나, 아무 일 없어 보일 수도 있어 디버깅이 까다로움

### 무효화 규칙

- 재할당이 일어나면 `vector`의 모든 반복자/포인터/참조가 무효화 됨
- 재할당 여부는 컴파일 타임에 알 수 없으므로, 삽입 연산 뒤에는 모두 무효화될 수 있다고 가정해야 안전함

| 연산                                                  | 무효화되는 대상                                         |
| ----------------------------------------------------- | ------------------------------------------------------- |
| `push_back` / `emplace_back` / `insert` (재할당 발생) | 모든 반복자, 포인터, 참조                               |
| `push_back` / `emplace_back` (재할당 없음)            | `end()` 반복자만                                        |
| `insert` / `erase` (재할당 없음)                      | 변경 지점 및 그 이후의 모든 요소 (반복자, 포인터, 참조) |
| `reserve` (capacity 증가 시)                          | 모든 반복자, 포인터, 참조                               |
| `shrink_to_fit`, `resize` (재할당 발생 시)            | 모든 반복자, 포인터, 참조                               |

### 가능한 버그 패턴

- 엔티티를 벡터로 관리하면서 특정 요소의 포인터를 따로 들고 있다가 문제가 생기는 경우
  
#### 요소 포인터를 저장해 두고 벡터에 추가

```cpp
std::vector<Monster> monsters;
Monster* boss = &monsters[0];
monsters.push_back(Monster{});    // 재할당 가능
boss->Attack();                   // 댕글링
```

#### 범위 기반 for 중 추가

```cpp
for (auto& m : monsters) {
    if (m.hp == 0) monsters.push_back(Monster{});  
    // 반복자 무효화 → UB
}
```

### 해결 방법

- 포인터 대신 인덱스 저장하기
  - 다만 중간 요소를 삭제하면 뒤 인덱스가 밀리므로, 삭제가 잦다면 `slot map`이나 `generational index` 같은 핸들 방식을 쓸 것
- 포인터 안정성이 필요하다면 `unique_ptr` 간접 저장 사용
- `reserve`로 미리 용량 확보하기.
  - 대신 최대 개수를 확실하게 알아야 함
  - 추가 capacity를 넘지 않는다는 보장이 있어야 함

#### `unique_ptr` 간접 저장

- `vector<unique_ptr<T>>`는 vector buffer에 포인터만 두고, 실제 오브젝트는 힙에 따로 할당함
- 재할당 시 옮겨지는 건 포인터 값 뿐이라 오브젝트 주소는 바뀌지 않음
- 하지만, 데이터들이 연속적으로 저장되는 것을 보장하지 않음
- `vector`에는 포인터만 저장되어 있고, element의 객체는 각각 할당되기 때문임
- 따라서, 캐시 친화율을 고려하여 `vector`를 사용한 것이라면 이 방법은 부적절할 수 있음

## 인용한 문서
• microsoft/STL — MSVC 표준 라이브러리 공식 저장소 (Apache-2.0 WITH LLVM-exception)

[https://github.com/microsoft/STL](https://github.com/microsoft/STL)