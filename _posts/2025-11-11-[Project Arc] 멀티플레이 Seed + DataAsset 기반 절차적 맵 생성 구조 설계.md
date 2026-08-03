---
title: "[Project Arc] 멀티플레이 Seed + DataAsset 기반 절차적 맵 생성 구조 설계"
description: "이번 작업에서는 멀티플레이 환경에서 동일한 Seed와 DataAsset을 기반으로 모든 클라이언트가 동기화된 절차적 맵을 생성할 수 있는 구조를 설계하였습니다."
date: 2025-11-11T06:19:27.389Z
tags: ["Project ARC","UE5"]
thumbnail: /assets/images/old/96420220-9e60-4817-8c0f-f5bd4a21c733-image.png
---
이번 작업에서는 멀티플레이 환경에서 동일한 Seed와 DataAsset을 기반으로 모든 클라이언트가 동기화된 절차적 맵을 생성할 수 있는 구조를 설계하였습니다. 본 글에서는 해당 구조를 체계적으로 정리하고 시각화하여 이해를 돕고자 합니다.

## 목표
- 멀티플레이에서 서버 결정적(Deterministic) 맵 생성
- Seed + DataAsset 조합으로 재현 가능한(Room Layout 재생성 가능) 상태 확보
- 방(Room) 타입 다양성: Monster / Treasure / Boss
- 확장 가능한 MapGenerateLogic / SpawnPositionSelector 컴포넌트 구조
- QuadTree 기반 공간 분할 예정 (Room 배치 탐색, 충돌 최소화, 성능 향상)

## 클래스 요약
- ACMProcedualMapGenerator: 맵 생성 중심 Actor, ICMMapGenerate 구현
- ICMMapGenerate: GenerateMap(Seed, DataAsset) 인터페이스 제공
- UCMRoomDataAsset: 맵 메타 정보 (Width, Height, MaxRoomCount, 방 클래스 목록)
- UCMMapGenerateLogicBaseComponent: 실제 배치 알고리즘/전략 확장 지점
- UCMSpawnPositionSelectorBaseComponent: 플레이어 스폰 위치 선택 로직 확장 지점
- ACMRoom: 개별 방 Actor (Monster/Treasure/Boss 등 파생 BP로 다양화)

## 맵 생성 흐름
- 서버: Seed 결정 → DataAsset 로드 → GenerateMap 호출 → 결과(방 좌표/타입) 확정
- 서버: 결과 구조(간단 좌표/타입 목록)만 복제(Replication) 또는 RPC 전송
- 클라이언트: 동일 Seed + DataAsset 참조로 재구성(경우에 따라 완전 재생성 또는 서버 결과 직접 적용)
- 재현성 확보: FRandomStream(Seed) 사용 → 순서/연산 규칙 고정

## QuadTree 도입 이유
- 현재 기획은 '마비노기'나 'The Binding of Isaac'같이 가지처럼 뻗어나가는 랜덤 지형 생성이 필요
- 2차원 배열을 이용하여 Grid한 구조를 사용할 경우 메모리가 낭비됨 등

## QuadTree 활용 계획 (추가 컴포넌트/구조 예상)
- 노드 구조: Bounds(Rect), Children[4], OccupiedRooms(List)
- 삽입 규칙: 미정, Map Generate Component에서 구현 예정
- 검색: TMap<FRoomPosition, Node>를 활용하여 해당 위치에 방이 이미 생성됐는지 확인 (O(1))
- 최적화: 방 배치 중 실패 횟수 증가 시 노드 깊이 제한 or 재시도 횟수 제한 적용

## GenerateMap 주요 단계(초안)
- 입력 검증: Seed > 0, DataAsset 유효성
- 랜덤 초기화: FRandomStream Stream(Seed)
- QuadTree 초기화: 루트 Bounds = (0,0)-(Width,Height)
- 필수 방 후배치: 맵의 가장 끝에 보스룸 생성(미정)
- 반복 배치: MaxRoomCount 도달까지 후보 위치 샘플링
- 충돌 검사: TMap<FRoomPosition, Node>을 활용

## 클래스 관계 (현재 + 계획)
![](/assets/images/old/96420220-9e60-4817-8c0f-f5bd4a21c733-image.png)

## Flowchart (방 배치 루프)
![](/assets/images/old/d281deb3-d29b-4e1f-9b7a-a4c394192275-image.png)


## 네트워크 고려 사항
- 복제 최소화: 방 전체 Actor 복제보다 구조(좌표+타입+클래스 Path)만 송신 후 클라이언트 Spawn
- 안정성: DataAsset Primary ID 사용 (서버/클라 동일 로드 보장)
- 재동기화: 새 플레이어 조인 시 Seed + 전체 Layout 재송신

## 성능 포인트
- QuadTree 삽입 O(log N) 기대, 충돌 검사 비용 절감
- 가중치 기반 타입 결정 시 누적 확률 사전 계산

## 확장 아이디어
- 방 연결(문/복도) 그래프 생성 및 경로 탐색 가중치 반영
- 플레이어 진행도 기반 동적 재배치(미구현, 설계 분리 필요)
- 시드 파생: 월/일/이벤트 기반 Daily Seed 시스템
- 맵 난이도 곡선 적용: 깊이(QuadTree 레벨)에 따라 몬스터 강도 증가

## 결론
이번 설계는 멀티플레이 환경에서 결정적이며 확장 가능한 절차적 맵 생성 체계를 수립하는 것을 목표로 하였으며, Seed와 DataAsset을 결합하여 재현성과 다양성을 동시에 확보할 수 있도록 구성하였습니다. 특히 QuadTree를 통한 공간 분할 기법을 적용할 계획을 통해 성능과 충돌 검사를 효율화하고 향후 난이도 곡선 및 특수 방 배치 전략에도 유연하게 대응할 수 있는 기반을 마련하였습니다. 앞으로 제안된 단계별 구현과 테스트 전략을 순차적으로 수행하여 안정적인 맵 생성 시스템을 완성하도록 하겠습니다.

