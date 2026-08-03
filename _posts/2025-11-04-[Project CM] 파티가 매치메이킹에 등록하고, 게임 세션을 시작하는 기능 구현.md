---
title: "[Project CM] 파티가 매치메이킹에 등록하고, 게임 세션을 시작하는 기능 구현"
description: "이번 작업에서는 로비에서 팀 전원이 Ready 상태가 되면 매치메이킹 큐에 팀을 올리고, 큐에 쌓인 팀 수가 임계치에 도달하면 GameSession을 시작하도록 서버 주도 로직을 직접 구현했습니다."
date: 2025-11-04T10:53:18.010Z
tags: ["Project CM","UE5"]
image:
  path: /assets/images/old/e69471a6-ee1f-403b-945d-c5c2a8c83995-image.png
categories: [Project CM + Project Arc]
---
이번 작업에서는 로비에서 팀 전원이 Ready 상태가 되면 매치메이킹 큐에 팀을 올리고, 큐에 쌓인 팀 수가 임계치에 도달하면 GameSession을 시작하도록 서버 주도 로직을 직접 구현했습니다. 

## 목표/요구사항
- 팀 내 모든 인원이 Ready가 되면 해당 팀을 매치메이킹 대기열에 추가합니다.
- 대기열의 팀 수가 RequiredTeamsToStart 이상이면 세션을 시작합니다.
- 로비에서 준비/취소/초대/합류/퇴장과 같은 상호작용이 자연스럽게 이어지도록 합니다.
- 서버 권한 강제, 중복 삽입 방지, 초기 동기화 타이밍 이슈를 예방합니다.

## 아키텍처 요약
- Team 상태 관리
  - FCMLobbyTeamInfo: TeamID, CurrentPlayerCount, ReadyPlayerCount, TeamMembers, TeamLeader 등으로 구성합니다.
  - Player별 PlayerStateLobby가 자신의 팀 정보를 캐싱합니다.
- Ready 처리 흐름
  - ReadyMatchmaking: 서버 전용으로 Ready 수를 올리고, 전원이 Ready면 EnterMatchmakingQueue를 호출합니다.
  - EnterMatchmakingQueue: 서버 전용으로 대기열(TeamID 집합)에 추가하고, 임계치 도달 시 StartGameSession을 호출합니다.
- Team 구성/합류
  - AddTeamToLobby: 새 플레이어 로그인 시 1인 팀을 생성하고 PlayerTeamMapping을 갱신합니다.
  - JoinTeam: 초대 수락 시 팀에 합류하며 인원 수와 초대 가능 상태를 갱신합니다.
- 초기 동기화
  - GameStateBase: OnLoadCompleted 이후 클라이언트가 로비 플레이어 목록 동기화를 수행합니다.
  - GameStateLobby: SyncLobbyPlayerList로 KnownLobbyPlayers를 갱신하고 Delegate를 브로드캐스트합니다.

## 핵심 흐름
- 로그인: CMGameModeLobby::PostLogin → CMGameStateLobby::AddTeamToLobby를 호출합니다.
- 초대/수락: PerformInvitePlayer → AcceptInvitePlayer → JoinTeam/RemoveLookingPlayer로 이어집니다.
- Ready: ReadyMatchmaking → EnterMatchmakingQueue → StartGameSession 순서로 진행됩니다.
- 동기화: GameStateBase 로드 시퀀스 완료 → CMGameStateLobby::SyncLobbyPlayerList가 실행됩니다.

### 소스 코드: Ready → 큐 진입 → 세션 시작
```cpp
// filepath: Source/CrimsonMoon/Private/Game/CMGameStateLobby.cpp
void ACMGameStateLobby::ReadyMatchmaking(FCMLobbyTeamInfo* TeamInfo)
{
    if (!TeamInfo)
    {
        UE_LOG(LogTemp, Warning, TEXT("ACMGameStateLobby::ReadyMatchmaking - TeamInfo is null"));
        return;
    }

    if (!HasAuthority())
    {
        UE_LOG(LogTemp, Warning, TEXT("ACMGameStateLobby::ReadyMatchmaking - Should be called on server only"));
        return;
    }

    // 이미 대기열에 있으면 무시
    if (MatchmakingQueueTeamIDs.Contains(TeamInfo->TeamID))
    {
        UE_LOG(LogTemp, Verbose, TEXT("ACMGameStateLobby::ReadyMatchmaking - Team %d already queued"), TeamInfo->TeamID);
        return;
    }

    // 준비 수 증가 (과증가 방지)
    TeamInfo->ReadyPlayerCount = FMath::Clamp(TeamInfo->ReadyPlayerCount + 1, 0, TeamInfo->CurrentPlayerCount);

    if (TeamInfo->CurrentPlayerCount > 0 && TeamInfo->ReadyPlayerCount >= TeamInfo->CurrentPlayerCount)
    {
        UE_LOG(LogTemp, Log, TEXT("ACMGameStateLobby::ReadyMatchmaking - Team %d is fully ready (%d/%d)"), TeamInfo->TeamID, TeamInfo->ReadyPlayerCount, TeamInfo->CurrentPlayerCount);
        EnterMatchmakingQueue(TeamInfo);
    }
    else
    {
        UE_LOG(LogTemp, Log, TEXT("ACMGameStateLobby::ReadyMatchmaking - Team %d ready progress: %d/%d"), TeamInfo->TeamID, TeamInfo->ReadyPlayerCount, TeamInfo->CurrentPlayerCount);
    }
}

void ACMGameStateLobby::EnterMatchmakingQueue(FCMLobbyTeamInfo* TeamInfo)
{
    if (!TeamInfo)
    {
        UE_LOG(LogTemp, Warning, TEXT("ACMGameStateLobby::EnterMatchmakingQueue - TeamInfo is null"));
        return;
    }

    if (!HasAuthority())
    {
        UE_LOG(LogTemp, Warning, TEXT("ACMGameStateLobby::EnterMatchmakingQueue - Should be called on server only"));
        return;
    }

    if (TeamInfo->TeamID < 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("ACMGameStateLobby::EnterMatchmakingQueue - Invalid TeamID"));
        return;
    }

    if (!MatchmakingQueueTeamIDs.Contains(TeamInfo->TeamID))
    {
        MatchmakingQueueTeamIDs.Add(TeamInfo->TeamID);
        UE_LOG(LogTemp, Log, TEXT("ACMGameStateLobby::EnterMatchmakingQueue - Team %d entered queue. QueueSize=%d"), TeamInfo->TeamID, MatchmakingQueueTeamIDs.Num());
    }
    else
    {
        UE_LOG(LogTemp, Verbose, TEXT("ACMGameStateLobby::EnterMatchmakingQueue - Team %d already in queue. QueueSize=%d"), TeamInfo->TeamID, MatchmakingQueueTeamIDs.Num());
    }

    // 기준 팀 수에 도달하면 게임 세션 시작
    if (MatchmakingQueueTeamIDs.Num() >= RequiredTeamsToStart)
    {
        StartGameSession();
        // 간단 구현: 시작 후 대기열 초기화 (중복 트리거 방지)
        MatchmakingQueueTeamIDs.Empty();
    }
}

void ACMGameStateLobby::StartGameSession()
{
    UE_LOG(LogTemp, Log, TEXT("ACMGameStateLobby::StartGameSession - Starting game session (RequiredTeamsToStart=%d)"), RequiredTeamsToStart);
}
```

### 소스 코드: 팀 생성/합류
```cpp
// filepath: Source/CrimsonMoon/Private/Game/CMGameStateLobby.cpp
void ACMGameStateLobby::AddTeamToLobby(ACMPlayerStateLobby* NewPlayer)
{
    FCMLobbyTeamInfo NewTeam;
    NewTeam.TeamID = TeamIndexCounter;
    NewTeam.CurrentPlayerCount = 1;
    NewTeam.TeamMembers.Add(NewPlayer);
    NewTeam.TeamLeader = NewPlayer;

    // 먼저 맵에 저장하여 영속적인 스토리지에 배치한 후, 그 참조를 캐싱합니다
    LobbyTeams.Add(TeamIndexCounter, NewTeam);
    FCMLobbyTeamInfo& StoredTeam = LobbyTeams[TeamIndexCounter];

    NewPlayer->SetCachedTeamInfo(&StoredTeam);
    PlayerTeamMapping.Add(NewPlayer->GetPendingNickname(), StoredTeam.TeamID);
    UE_LOG(LogTemp, Log, TEXT("ACMGameStateLobby::AddTeamToLobby - Added new team with ID %d"), StoredTeam.TeamID);

    TeamIndexCounter++;
}

void ACMGameStateLobby::JoinTeam(const FName& JoinedPlayer, const FName& JoiningPlayer)
{
    if (ACMPlayerControllerLobby* PC = CurrentLookingPlayers[JoiningPlayer])
    {
        int32 TeamIndex = PlayerTeamMapping[JoinedPlayer];
        if (LobbyTeams.Contains(TeamIndex))
        {
            FCMLobbyTeamInfo& TeamInfo = LobbyTeams[TeamIndex];
            TeamInfo.CurrentPlayerCount++;
            if (ACMPlayerStateLobby* PS = PC->GetPlayerState<ACMPlayerStateLobby>())
            {
                TeamInfo.TeamMembers.Add(PS);
                PS->SetCachedTeamInfo(&TeamInfo);
                PS->SetCanBeInvited(false);
            }
            UE_LOG(LogTemp, Log, TEXT("ACMGameStateLobby::JoinTeam - Player %s joined team %d"), *JoinedPlayer.ToString(), TeamIndex);
        }
    }
}
```

## 안정성/중복/권한 처리
- 서버 전용 메서드를 HasAuthority로 보호하여 ReadyMatchmaking/EnterMatchmakingQueue가 서버에서만 실행되도록 했습니다.
- 대기열 중복은 MatchmakingQueueTeamIDs.Contains 검사로 차단했습니다.
- TeamID 유효성을 확인하여 음수 값을 방지했습니다.
- Ready 카운트는 FMath::Clamp로 과증가를 방지했습니다.
- 초기 동기화 타이밍은 GameState 미존재 시 다음 틱 재시도로 레이스를 완화했습니다.

## 에지 케이스
- 팀 인원이 0명일 때는 ReadyMatchmaking에서 처리하지 않도록 했습니다.
- 동일 팀에서 Ready가 중복 호출되면 이미 큐에 있음을 감지하고 조기 반환합니다.
- PlayerState 복제 지연 상황에서 OnRep/다음 틱 재시도로 안전하게 동기화를 완료합니다.
- 초대 수락 직후 Ready 호출 시 TeamInfo 일관성을 유지하도록 합류 로직 이후 상태를 점검합니다.

## 실제 적용
![](/assets/images/old/e69471a6-ee1f-403b-945d-c5c2a8c83995-image.png)

## 마치며
팀 전원이 Ready가 되면 큐에 진입하고, 큐의 팀 수가 임계치에 도달하면 세션을 시작하는 핵심 사용자 여정을 서버 권한, 중복 방지, 복제 타이밍을 고려하여 직접 구현했습니다. 현재 구조는 확장에 용이하며, Ready 취소/퇴장 처리와 실제 세션 전환(맵 트래블)을 보강하면 실전 매치메이킹 파이프라인으로 무리 없이 연결될 것으로 판단됩니다.

