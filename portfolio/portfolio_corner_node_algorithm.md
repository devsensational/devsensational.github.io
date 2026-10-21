---
layout: page
title: "MR 환경 내비게이션 개발 프로젝트"
permalink: /portfolio/portfolio_corner_node_algorithm/
---

## 프로젝트 개요

{% include embed/youtube.html id='NlATkbd4m8E' %}

- **프로젝트 명:** MR환경 내비게이션 프로젝트
- **역할**
    - Topology Map 생성 알고리즘 개발
    - MR 환경 내비게이션 앱 개발
    - 프로젝트 통합 및 리딩
    - 문서화
- **개발 환경**
    - Unity 2020.3.25f1
    - C#
    - HoloLens 2/MR
- **기간:** 2022.01 ~ 2022.12
- **인원:** 3명
- **논문 링크:** [A Topology Map Generation Algorithm for Optimal Path Finding for Image-Based Maps](https://www.mdpi.com/2076-3417/12/23/12436)
(Applied Sciences, MDPI · SCIE · 2022 JIF 2.7 · 2022.12 게재 · 1저자)

---

## 프로젝트 배경

- MR 기반 **실내 재난 모니터링 및 구조 시스템 연구**의 일부
- 기존 방식으로 얻을 수 있는 건물 구조 **데이터가 제한적** → 도면 기반으로 **빠르게 Topology Map 생성** 필요
- PC에서 Grid 기반 A\* 탐색 시간을 먼저 측정한 결과, PC보다 성능이 낮은 HMD에서 실행하면 **실시간 경로 갱신이 어렵고 배터리 소모가 늘어날 것**으로 판단
- 구조 임무 특성상 **정확한 경로 안내**가 필요
- 적절한 Pathfinding 최적화가 요구되어 자체 알고리즘 연구 진행

---

## 전체 요약

- **Mixed Reality(MR)** 환경 실내 내비게이션 시스템 개발
- 자체 개발 **CNA 알고리즘**으로 도면 기반 그래프 생성
- A\* 탐색 시 **방문 노드 수 99.82~99.95% 감소**
- **Unity + MRTK** 기반 MR 안내 시스템 구현
- **MDPI Applied Sciences(SCI-E) 논문 1저자, 경진대회 금상, 특허 등록**

![image.png](/assets/images/portfolio_corner_node_algorithm_images/image.png)

![image.png](/assets/images/portfolio_corner_node_algorithm_images/image%201.png)

- 팀 리딩(회의/문서화/커뮤니케이션)

---

## 주요 구현 내용

### 1. 도면 기반 Topology Map 생성 알고리즘 (CNA)

![Topology Map 생성 결과물](/assets/images/portfolio_corner_node_algorithm_images/7.png)
_Topology Map 생성 결과물_

**A\* 탐색 시 방문 노드 수 (평균)**

| **Complexity**       | **A\* 단독** | **A\* + CNA** | **감소율** |
| -------------------- | ------------ | ------------- | ---------- |
| **Very Simple**      | 46062.5      | 39            | −99.92%    |
| **Simple**           | 122703       | 102.2         | −99.92%    |
| **Intermediate**     | 107462.6     | 147.2         | −99.86%    |
| **Complicated**      | 176671.1     | 200.8         | −99.89%    |
| **Very Complicated** | 759311.4     | 380.8         | −99.95%    |
| **Special Case**     | 143376.6     | 260           | −99.82%    |

_방문 노드 수 = Open List + Close List 노드 수의 합, 맵당 시나리오 10개 평균_

| 기능               | 설명                                                                                     |
| ------------------ | ---------------------------------------------------------------------------------------- |
| 이미지 → Grid 변환 | 도면 이미지를 2D 배열(Grid)로 변환 (**팀원 담당**, 본인은 변환된 데이터를 입력으로 사용) |
| 노드 생성          | 벽 영역에서 **코너 검출 후 노드 생성**                                                   |
| 그래프 구성        | 생성된 노드들을 연결해 **Topology Map 구축**                                             |
| 최적화             | A\* 탐색 시 방문 노드 수 **99.82~99.95% 감소**                                           |

#### 핵심 포인트

- 고해상도 도면에서는 모든 픽셀이 노드가 되고, 직선거리 휴리스틱이 직선거리는 가깝지만 막혀 있는 구역 쪽으로 탐색을 끌어당겨 방문 노드가 급증함
- CNA로 장애물의 코너에만 노드를 만들어 탐색 대상 노드 수를 줄임
- 검증: 미로 5개 예시에서 정답 경로와 같은 결과, 미로 100개에서 Topology Map 생성과 경로 탐색 성공
- 한계: 대각선 벽은 픽셀 단위 계단 형태로 저장되어 코너로 인식되므로 노드가 과다 생성되고 전처리 시간이 늘어남

---

### 2. A* Algorithm 기반 경로 탐색

![생성된 Topology Map에 A\*를 적용한 결과물](/assets/images/portfolio_corner_node_algorithm_images/13.png)
_생성된 Topology Map에 A\*를 적용한 결과물_

**A\* 단독 vs A\* + CNA 경로 탐색 시간 (평균)**

| **Complexity**       | **전처리 시간 (CNA)** | **A\* 단독** | **A\* + CNA** | **탐색 시간 감소율 (전처리 제외)** |
| -------------------- | --------------------- | ------------ | ------------- | ---------------------------------- |
| **Very Simple**      | 7 ms                  | 75.8 ms      | 1.2 ms        | -98.42%                            |
| **Simple**           | 46.2 ms               | 264.2 ms     | 2.5 ms        | -99.05%                            |
| **Intermediate**     | 90.4 ms               | 183.8 ms     | 2.8 ms        | -98.48%                            |
| **Complicated**      | 280.8 ms              | 775.5 ms     | 6.7 ms        | -99.14%                            |
| **Very Complicated** | 1137.2 ms             | 3342.1 ms    | 9.7 ms        | -99.71%                            |
| **Special Case**     | 582.8 ms              | 557.6 ms     | 5.5 ms        | -99.01%                            |

- 측정 환경: Intel i7-1260P / DDR4 16GB / Intel Iris Xe / Windows 11 21H2 / Unity 2020.3.25f1 (PC). 맵당 시나리오 10개 평균, 출발–도착 직선거리 100 이상, 경로가 없는 시나리오 제외
- 전처리는 맵마다 1회 수행하고, 건물 구조가 바뀌지 않으면 생성된 Topology Map을 재사용합니다. Special Case처럼 전처리 시간이 A\* 단독 탐색보다 긴 맵도 있어, 같은 맵에서 탐색을 반복할수록 이득이 커집니다.


| 항목          | 내용                                                   |
| ------------- | ------------------------------------------------------ |
| 탐색 알고리즘 | A\* (Straight-line Distance Heuristic)                 |
| 적용 대상     | CNA로 생성한 Topology Map Graph                        |
| 효과          | PC 측정 기준 탐색 시간 98.42~99.71% 감소 (전처리 제외) |

#### 핵심 포인트

- 목적지까지의 **직선 거리(Heuristic)** 사용
- CNA로 만든 Topology Map 위에서 탐색해 **방문 노드 수를 줄임**
- Grid 기반 A\* 대비 **탐색 시간 98.42~99.71% 감소** (PC, 전처리 제외)

---

### 3. MR 내비게이션 시스템 구현 (Unity + MRTK)

![목적지 지정](/assets/images/portfolio_corner_node_algorithm_images/30.png)
_목적지 지정_

![경로 안내](/assets/images/portfolio_corner_node_algorithm_images/28.png)
_경로 안내_

| 기술         | 내용                                                                                                      |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| 엔진         | Unity                                                                                                     |
| MR Framework | MRTK(Mixed Reality Toolkit)                                                                               |
| 기능         | 하단 UI에서 목적지를 선택하고 Start를 누르면 경로를 생성해 **미니맵과 실제 공간 위 가상 오브젝트**로 표시 |
| 결과         | 사용자가 건물 구조를 몰라도 HoloLens 2 화면의 안내를 따라 이동할 수 있는 내비게이션 구현                  |

#### 핵심 포인트

- Unity + MRTK로 HoloLens 2용 앱을 구성하고 목적지 선택 UI 구현
- 생성된 경로를 **미니맵**과 **실제 공간 위 가상 오브젝트** 두 곳에 표시

---

## 프로젝트 매니지먼트

| 항목         | 수행 내용                                                |
| ------------ | -------------------------------------------------------- |
| 회의 관리    | 주간 회의를 주관, 이슈 공유 및 주간 목표 설정            |
| 문서화       | 진행 상황·회의록 작성 → Google Cloud로 공유              |
| 커뮤니케이션 | Git·Discord·KakaoTalk 기반 실시간 이슈 관리 및 화면 공유 |
| 협업 문화    | 문제 상황을 팀 단위로 즉시 공유하여 빠르게 해결          |

#### 핵심 포인트

- 팀 리딩 역할 수행
- 문서화 및 커뮤니케이션 체계적 운영
- 실시간 협업 환경 구축으로 프로젝트 효율 향상

<br><br>

<div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
  <a href="/portfolio/" style="display: inline-block; padding: 14px 28px; font-size: 1.05rem; font-weight: 600; color: #495057; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 8px; text-decoration: none; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease-in-out;">
    <i class="fas fa-arrow-left" style="margin-right: 8px; color: #6c757d;"></i> 포트폴리오 리스트로 돌아가기
  </a>
</div>
