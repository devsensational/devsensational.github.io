---
title: Stack Overflow vs Stack Buffer Overflow
date: 2026-09-26 13:44 +0900
category: [Computer Science]
tags: ["computer science"]
description: 넘는 경계의 차이와 방향이 만드는 피해 범위
image:
  path: /assets/images/2026-09-26-overflow/2.png
math: true
---

블로그 글 스타일을 변경하고 AI 생성 이미지를 실험적으로 도입중입니다. 관련 내용은 이전 글을 참조해주시면 감사합니다.

## 요약

|               | 스택 오버플로                              | 스택 버퍼 오버플로                      |
| ------------- | ------------------------------------------ | --------------------------------------- |
| 무엇이 넘치나 | 스택 전체                                  | 스택 위의 배열 하나                     |
| 넘치는 방향   | 아래 (SP 성장 방향)                        | 주로 위 (쓰기 방향, 음수 인덱스는 아래) |
| 원인          | 깊은 재귀, 큰 지역 변수                    | 범위 밖 쓰기, 길이 미확인 복사          |
| 결과          | OS가 즉시 감지해 크래시                    | 조용히 데이터 손상, 나중에 크래시       |
| 보안 문제     | 가드에 걸리면 크래시, 건너뛰면 Stack Clash | 대표적인 취약점                         |

## 방향

![](/assets/images/2026-09-26-overflow/2.png)

- 스택은 높은 주소 → 낮은 주소로 자람 (x86/x64/ARM 등 주요 ABI 기준, C++ 표준이 정하는 것은 아님)[^1]
- 배열 인덱스는 낮은 주소 → 높은 주소로 증가 (C++ 표준이 보장)[^2]
- 두 "방향"은 서로 다른 축
  - 스택: SP가 움직이는 방향 (할당)
  - 배열: 쓰기 주소가 움직이는 방향 (인덱스)
- **두 문제는 넘는 경계로 구분, 방향 차이는 피해 범위를 설명**[^3]
  - 버퍼 쓰기는 위로 → 이미 쌓인 복귀 주소를 덮음
  - 가드 페이지는 아래 → 위로 가는 쓰기를 못 막음

![](/assets/images/2026-09-26-overflow/4.png)

## 스택 오버플로

- 스택 **전체**가 최대 크기를 넘는 것
- 스택은 0번지까지가 아니라 정해진 한계까지만 자람
- 원인
  - 너무 깊은 재귀
  - 큰 지역 배열 (`int a[10000000];`)
- 한계를 넘어 가드 페이지를 건드리면 발생

### 가드 페이지

- Windows: 커밋된 영역 바로 아래에 붙어서 스택과 함께 이동[^4]
  - 최대 크기만큼 reserve, 필요한 만큼만 commit
  - 가드 페이지 접근 시 OS가 커밋하고 가드를 한 칸 아래로 옮김[^5]
  - 예약 영역 끝에서 더 못 옮기면 스택 오버플로
- Linux pthread 스택: 맨 아래 경계에 고정, 접근 시 `SIGSEGV`[^6]
- 큰 지역 배열은 가드 페이지를 건너뛸 수 있어서 컴파일러가 스택 프로브(MSVC `_chkstk`, x86 4KB / x64 8KB 초과 시)를 삽입[^7]
  - 건너뛰면 가드 아래의 다른 메모리(힙 등)를 스택으로 쓰게 됨 → Stack Clash 공격
  - GCC는 `-fstack-clash-protection`으로 한 페이지씩 할당·접근해 건너뛰기를 막음[^8]

## 스택 버퍼 오버플로

- 스택 위 **배열 하나**의 범위를 넘어 쓰는 것
- 스택 공간이 남아 있어도 발생
- 배열 끝을 넘는 쓰기는 위로 가므로 이미 쌓인 데이터를 덮음
  - (`/GS` 사용 시) 보안 쿠키 → 저장된 레지스터 → 복귀 주소 → 호출한 함수의 프레임 순[^9]
  - 같은 프레임의 다른 지역 변수 배치는 컴파일러 재량
  - 가드 페이지는 반대쪽이라 막지 못함
- 음수 인덱스 등 시작 앞 쓰기(underwrite)는 아래로 감[^3]

![](/assets/images/2026-09-26-overflow/3.png)

- 원인
  - 범위 검사 없는 쓰기, off-by-one (`i <= N`)
  - `strcpy`, `sprintf`, `gets` 등 길이 미확인 함수
  - `memcpy` 크기 오류
- 증상
  - 쓰는 순간이 아니라 주로 **return 시점**에 크래시 (`/GS` 검사가 함수 종료 시 수행)[^9]
  - 덮인 지역 변수·포인터를 return 전에 쓰면 더 일찍 크래시
  - 콜스택이 깨져 보임
  - VS Debug 빌드의 "Stack around the variable ... was corrupted"
- 방어
  - 스택 카나리 (`/GS`, `-fstack-protector`)
  - ASLR, DEP
  - 경계를 지키는 도구 (`std::array`, `std::vector`, `std::string`)

### scanf

- `scanf("%s", buf)`는 버퍼 크기를 모르고 길이 제한 없이 씀
- `%[^\n]`도 동일, `gets`는 같은 이유로 표준에서 삭제
- VS C4996 경고의 이유, `_CRT_SECURE_NO_WARNINGS`는 경고만 끌 뿐
- 해결
  - `scanf("%15s", buf)` (널 문자 자리 1칸 제외)
  - `scanf_s("%s", buf, 16)` (MSVC)
  - `fgets(buf, sizeof(buf), stdin)`
- `scanf("%d", &n)`은 오버플로 없음, 단 `&` 누락 시 다른 메모리 손상

### int 배열

- 타입 무관, 스택의 모든 배열에서 발생 (int가 4바이트인 환경에서 한 칸당 4바이트 손상)
- 입력받은 개수만큼 배열에 넣는 코드에서 흔한 실수
- 함수 매개변수 `int a[]`는 실제로 포인터
  - `sizeof(a)`는 포인터 크기 (64비트 8, 32비트 4)
  - 길이를 몰라 범위 초과가 쉬움
  - C는 길이를 함께 전달, C++은 `std::array`, `std::vector`, `std::span`

## 오류 코드

- 둘 다 C++ 예외가 아님 → 기본(`/EHsc`)에서는 `try/catch`로 못 잡음
  - `/EHa`면 `catch(...)`가 SEH 예외도 받지만 복구는 여전히 어려움[^10]
- Windows
  - 스택 오버플로: `0xC00000FD`
  - `/GS` 감지 스택 버퍼 오버플로: `0xC0000409`
  - 감지 못 하고 망가진 주소로 점프: 보통 `0xC0000005`
  - `0xC00000FD`는 SEH로 잡을 수는 있으나 복구가 어려움
  - `0xC0000409`는 SEH도 거치지 않고 즉시 종료, `__fastfail` 공용 코드라 다른 원인일 수도 있음[^11]
  - "Run-Time Check Failure #2"는 예외 코드가 아니라 `/RTC` 메시지

## 정리

- 스택 오버플로: 스택 전체가 아래로 넘침, 재귀·큰 지역 변수, 가드 페이지로 즉시 감지 (건너뛰면 Stack Clash)
- 스택 버퍼 오버플로: 배열 하나가 주로 위로 넘침, 복귀 주소 손상, 보안 취약점
- 구분은 **넘는 경계**, 피해 범위는 **방향** (스택은 아래로, 배열 인덱스는 위로)
- 전역 배열은 스택이 아니므로 두 "스택" 문제는 아님, 단 범위 밖 쓰기는 전역 버퍼 오버플로 (인접 전역 데이터 손상)[^12]


[^1]: [sigaltstack(2) — Linux manual page](https://man7.org/linux/man-pages/man2/sigaltstack.2.html)
[^2]: [Comparison operators — cppreference.com](https://en.cppreference.com/w/cpp/language/operator_comparison)
[^3]: [CWE-121: Stack-based Buffer Overflow — MITRE](https://cwe.mitre.org/data/definitions/121.html)
[^4]: [Thread Stack Size — Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/procthread/thread-stack-size)
[^5]: [Creating Guard Pages — Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/memory/creating-guard-pages)
[^6]: [pthread_attr_setguardsize(3) — Linux manual page](https://man7.org/linux/man-pages/man3/pthread_attr_setguardsize.3.html)
[^7]: [`_chkstk` Routine — Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/devnotes/-win32-chkstk)
[^8]: [Instrumentation Options (-fstack-clash-protection) — GCC](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
[^9]: [/GS (Buffer Security Check) — Microsoft Learn](https://learn.microsoft.com/en-us/cpp/build/reference/gs-buffer-security-check)
[^10]: [/EH (Exception handling model) — Microsoft Learn](https://learn.microsoft.com/en-us/cpp/build/reference/eh-exception-handling-model)
[^11]: [`__fastfail` — Microsoft Learn](https://learn.microsoft.com/en-us/cpp/intrinsics/fastfail)
[^12]: [AddressSanitizer — Clang](https://clang.llvm.org/docs/AddressSanitizer.html)
