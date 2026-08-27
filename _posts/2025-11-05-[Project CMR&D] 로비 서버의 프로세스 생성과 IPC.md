---
title: "[Project CM/R&D] 로비 서버의 프로세스 생성과 IPC"
description: "Project CM은 여러 개의 세션을 생성해야 할 필요가 있습니다. 로비에 모여있던 플레이어들은 매치메이킹을 통해 생성된 새로운 세션(서버)에 접속해서 게임을 플레이하는 구조이기 때문입니다."
date: 2025-11-05T10:13:11.422Z
tags: ["project cm","ue5","rnd"]
categories: [Project, Project CM + Project Arc]
---
Project CM은 여러 개의 세션을 생성해야 할 필요가 있습니다. 로비에 모여있던 플레이어들은 매치메이킹을 통해 생성된 새로운 세션(게임 서버 인스턴스)에 접속해서 게임을 플레이하는 구조이기 때문입니다.

UE5에서 새로운 세션은 처음 실행될 때 필연적으로 초기화 과정을 거치게 됩니다. 이 과정에서는 맵 로딩, 서브시스템 초기화, 데이터 로드 등 여러 환경 의존적인 작업이 수행되며, 상황에 따라 수 초 정도의 지연이 발생할 수 있습니다.

문제는 바로 이 시점에 있습니다. **로비 서버가 새 세션을 생성하자마자 클라이언트가 해당 서버로 접속을 시도할 경우, 서버가 아직 완전히 준비되지 않은 상태일 수 있습니다.** 이로 인해 환경 부하나 타이밍에 따라 연결 거부, 타임아웃(Timeout) 또는 랜덤하게 성공하는 불안정한 접속과 같은 Race Condition이 발생할 수 있습니다. **즉, 동일한 코드와 절차를 밟더라도 실행 타이밍에 따라 결과가 달라지는 비결정적인 상태가 생길 수 있는 것입니다.**

이를 방지하기 위해 저는 새로운 세션이 완전히 준비된 이후에만 클라이언트가 접속할 수 있도록 로비 서버와 게임 서버 간의 신호를 주고받는 구조를 설계하고자 합니다.

이를 구현하기 위한 기반 기술로 IPC(Inter-Process Communication, 프로세스 간 통신) 을 선택하였으며,
  포스트에서는 IPC의 개념과 주요 방식들을 먼저 정리하고, 이후 실제 UE5 환경에서 이를 어떻게 적용할지에 대해 단계적으로 학습하고자 합니다.
  
---

## 구상 배경

### 🔹 문제 상황

* UE5의 `Seamless Travel`이나 `ServerTravel`만으로는 프로세스 단위의 서버 분리를 완전히 제어하기 어려움
* 다수의 게임 세션을 독립적으로 관리해야 하는 상황 (예: 여러 방 동시 운영)
* 로비 서버는 유저 매칭/세션 준비만 담당하고, 실제 게임은 별도의 독립 프로세스 서버에서 진행되어야 함

### 🔹 목표

* 로비 서버가 새로운 서버 프로세스를 생성 (`GameServer.exe`)
* 새 서버가 부팅 완료 후 로비 서버로 “준비 완료” 신호를 IPC로 전달
* 로비 서버가 대기 중인 클라이언트들에게 접속 정보(IP, Port 등)를 전송
* 클라이언트는 해당 정보로 새 서버에 자동 접속

### 🔹 설계 핵심

* 프로세스 간 신호 교환을 **Socket 기반 통신**으로 구현
* Socket을 선택한 이유는 현 프로젝트에서는 언리얼에서 구현한 하나의 PC에서만 서버가 작동할 예정이지만, 실제 대형 프로젝트에서는 Port 개수의 제한, 클라우드 환경, 가상망 사용 등, 여러 제약에 의해 여러 대의 서버에서 작동할 수 있기 때문
* 로비 서버는 “마스터 서버”, 게임 서버는 “세션 프로세스” 역할

---

## IPC(Inter-Process Communication) 학습 정리

### 🔸 IPC란?

* 운영체제에서 서로 다른 프로세스 간 데이터를 주고받는 메커니즘
* 한 프로세스가 다른 프로세스의 메모리에 직접 접근할 수 없기 때문에 필요

### 🔸 IPC 주요 방식 정리

| 방식                       | 설명                         | 장점                       | 단점                        |
| -------------------------- | ---------------------------- | -------------------------- | --------------------------- |
| **Socket**                 | 네트워크 기반 통신 (TCP/UDP) | 확장성 높음, UE5 통합 용이 | 로컬 통신에는 오버헤드 있음 |
| **Named Pipe**             | OS가 제공하는 로컬 IPC       | 단순 신호 전달에 유용      | OS별 관리 차이 존재         |
| **Shared Memory**          | 메모리 맵 공유               | 매우 빠름                  | 동기화(Mutex) 필요          |
| **Message Queue / Signal** | 커널 기반 비동기 메시징      | 상태 신호용으로 적합       | UE5에서 직접 구현 복잡      |

---

## 현재 고려 중인 구조

* 로비 서버 ↔ 게임 서버 간 **TCP 소켓 기반 통신**
* 게임 서버 실행 시, 로비 서버의 특정 포트에 “ServerReady” 메시지 송신
* 로비 서버는 메시지 수신 후 클라이언트 세션에 접속 신호 송신

```cpp
// 서버 프로세스 생성 예시
FString CommandLine = TEXT("-Port=7777 -SessionID=1234");
FProcHandle ServerProc = FPlatformProcess::CreateProc(
    *ServerPath,
    *CommandLine,
    true,  // bLaunchDetached
    false, // bLaunchHidden
    false, // bLaunchReallyHidden
    nullptr,
    0,
    nullptr,
    nullptr
);
```

```cpp
// TCP 메시지 수신 예시
FSocket* ListenSocket = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateSocket(NAME_Stream, TEXT("LobbyListener"), false);
bool bBind = ListenSocket->Bind(*Addr);
bool bListen = ListenSocket->Listen(8);

while (bRunning)
{
    bool bHasPending;
    if (ListenSocket->HasPendingConnection(bHasPending) && bHasPending)
    {
        TSharedPtr<FSocket> ClientSocket = ListenSocket->Accept(TEXT("ServerConnection"));
        // "ServerReady" 수신 후 처리 로직
    }
}
```

### 🔹 예상 시퀀스 다이어그램

```text
[로비 서버] -> CreateProcess("GameServer.exe", Args)
               ↓
[게임 서버] -> 초기화 완료 시 "ServerReady" 신호 송신 (TCP)
               ↓
[로비 서버] -> 해당 세션 참가자들에게 접속 정보 전달
               ↓
[클라이언트] -> 새 서버로 자동 접속
```

---
## 세션을 미리 생성해 놓는다면?
세션을 미리 생성하게 되면 바로바로 유저들이 접속할 수 있겠지만, 유저들이 접속하지 않아도 자원을 점유한다는 점과 동시에 여러 유저가 접속하게 됐을 때 관리하기 어려울 수 있다는 것을 생각했습니다. 따라서, 접속 유저가 확정되었을 때 마다 세션을 생성하도록 결정했습니다. 

---

## 마치며

이번 구상은 단순히 서버를 나누는 수준을 넘어, **UE5 외부 시스템 수준에서의 프로세스 관리 및 통신 구조**를 고민하게 된 계기였습니다. 특히 IPC는 운영체제 레벨의 개념이지만, 이를 UE5 C++ 코드와 통합해 **실질적인 서버 간 메시징 구조**를 설계해야 하는 부분에서 많은 학습이 있었습니다.

