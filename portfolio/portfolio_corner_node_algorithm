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
    - Unity 2022
    - C#
    - HoloLens 2/MR
- **기간:** 2022.01 ~ 2022.12
- **인원:** 3명

논문 링크

[A Topology Map Generation Algorithm for Optimal Path Finding for Image-Based Maps](https://www.mdpi.com/2076-3417/12/23/12436)

---

## 프로젝트 배경

- MR 기반 **실내 재난 모니터링 및 구조 시스템 연구**의 일부
- 건물 구조 **데이터 부재** → 도면 기반으로 **빠르게 Topology Map 생성** 필요
- MR HMD의 **낮은 컴퓨팅 파워**, 구조 임무 특성 상 **오류 없는 경로 안내 필수**
- 적절한 Pathfinding 최적화가 요구되어 자체 알고리즘 연구 진행

---

## 전체 요약 (핵심 키워드)

- **Mixed Reality(MR)** 환경 실내 내비게이션 시스템 개발
- 자체 개발 **CNA 알고리즘**으로 도면 기반 그래프 생성
- Pathfinding **노드 수 90% 이상 감소**, A* 기반 경로 탐색
- **Unity + MRTK** 기반 MR 안내 시스템 구현
- **SCI-E 저널 논문 1저자, 경진대회 금상**

![image.png](/assets/images/portfolio_corner_node_algorithm_images/image.png)

![image.png](/assets/images/portfolio_corner_node_algorithm_images/image%201.png)

- 팀 리딩(회의/문서화/커뮤니케이션)

---

## 주요 구현 내용

### 1. 도면 기반 Topology Map 생성 알고리즘 (CNA)

![Topology Map 생성 결과물](/assets/images/portfolio_corner_node_algorithm_images/7.png)
*Topology Map 생성 결과물*

**그래프 정점 개수 감소율**

| **Complexity**       | **A***   | **A* With CNA** | **Percentage** |
| -------------------- | -------- | --------------- | -------------- |
| **Very Simple**      | 46062.5  | 39              | −99.92%        |
| **Simple**           | 122703   | 102.2           | −99.92%        |
| **Intermediate**     | 107462.6 | 147.2           | −99.86%        |
| **Complicated**      | 176671.1 | 200.8           | −99.89%        |
| **Very Complicated** | 759311.4 | 380.8           | −99.95%        |
| **Special Case**     | 143376.6 | 260             | −99.82%        |

| 기능               | 설명                                              |
| ------------------ | ------------------------------------------------- |
| 이미지 → Grid 변환 | 도면을 이미지 처리해 **타일맵 형태(Grid)**로 변환 |
| 노드 생성          | 벽 영역에서 **코너 검출 후 노드 생성**            |
| 그래프 구성        | 생성된 노드들을 연결해 **Topology Map 구축**      |
| 최적화             | Pathfinding에 필요한 노드 수 **90% 이상 감소**    |

#### 핵심 포인트

- 일반적인 A* 단독 적용 시 넓은 공간에서 **잘못된 경로** 생성 문제를 해결
- 도면 기반 그래프 생성(Corner Node Algorithm, CNA)을 통해 **정확한 노드만 추출**
- 결과적으로 **오류 없는 경로 + 고성능 탐색** 실현

#### 코드 스니펫

```csharp
// Corner Node Algorithm을 구현하는 클래스의 일부분입니다.
public class CornerNodeAlgorithmV2
{
    private int[,] direction = {
        {1, 0}, {1, 1}, {0, 1}, {-1, 1},
        {0, -1}, {-1, -1}, {-1, 0}, {1, -1}
    };
    
    private int width, height;

    private Cell[,] mapData;
    private List<PathNode> pNodeList = new List<PathNode>();
    private List<(int, int)> wallList;

    private void createCorner(int x, int y, int beforeDirection)
    {
        if (x < 0 || y < 0 || x >= width || y >= height)
            return; // Out of range

        if (mapData[x, y].Type == Constants.CHECK)
            return; // Checked cell

        if (mapData[x, y].Type == Constants.OPEN) // is Corner?
        {
            int wallCount = 0;

            for (int i = 0; i < 8; i++)
            {
                int nextX = x + direction[i, 0];
                int nextY = y + direction[i, 1];

                if (!(nextX < 0 || nextY < 0 || nextX >= width || nextY >= height))
                {
                    if (mapData[nextX, nextY].Type == Constants.WALL ||
                        mapData[nextX, nextY].Type == Constants.CHECK)
                    {
                        wallCount++;
                    }
                }

                if (wallCount > 1) break;
            }

            if (wallCount == 1)
            {
                mapData[x, y].Type = Constants.NODE;
                pNodeList.Add(new PathNode(x, y));
            }

            return;
        }

        if (mapData[x, y].Type == Constants.WALL)
        {
            mapData[x, y].Type = Constants.CHECK;

            int backward = directionSelector(beforeDirection - 4);

            for (int i = 0; i < 7; i++)
            {
                int nextDirection = directionSelector(backward + i);
                int nextX = x + direction[nextDirection, 0];
                int nextY = y + direction[nextDirection, 1];

                createCorner(nextX, nextY, nextDirection);
            }
        }
    }
}
```

---

### 2. A* Algorithm 기반 경로 탐색

![생성된 Topology Map에 A*를 적용한 결과물](/assets/images/portfolio_corner_node_algorithm_images/13.png)
*생성된 Topology Map에 A*를 적용한 결과물*

**A* 단일 적용 vs A* + 최적화 적용 결과 표**

| **Complexity**       | **Preprocessing Time** | **A***    | **A* with CNA** | **Percentage** |
| -------------------- | ---------------------- | --------- | --------------- | -------------- |
| **Very Simple**      | 7 ms                   | 75.8 ms   | 1.2 ms          | -90.77%        |
| **Simple**           | 46.2 ms                | 264.2 ms  | 2.5 ms          | -99.05%        |
| **Intermediate**     | 90.4 ms                | 183.8 ms  | 2.8 ms          | -98.48%        |
| **Complicated**      | 280.8 ms               | 775.5 ms  | 6.7 ms          | -99.14%        |
| **Very Complicated** | 1137.2 ms              | 3342.1 ms | 9.7 ms          | -99.71%        |
| **Special Case**     | 582.8 ms               | 557.6 ms  | 5.5 ms          | -99.01%        |

| 항목          | 내용                                                  |
| ------------- | ----------------------------------------------------- |
| 탐색 알고리즘 | A* (Straight-line Distance Heuristic)                 |
| 적용 대상     | CNA로 생성한 Topology Map Graph                       |
| 효과          | ↓ 노드 수 감소 → **MR HMD에서도 빠른 연산 속도 확보** |

#### 핵심 포인트

- 목적지까지의 **직선 거리(Heuristic)** 사용
- 그래프 기반 탐색으로 **경로 오류 제거**
- 기존 Grid 탐색 대비 **성능 대폭 향상**

#### 코드 스니펫

```csharp
// A* 알고리즘을 적용하기 위한 메소드입니다.
private void aStarAlgorithm(AStarNode ptr)
{
    do
    {
        ptr = addCloseList();
        addOpenList(ptr);
        
        if (ptr.GetNode == targetNode && ptr.GetNode == targetNode)
        {
            Debug.Log("Pathfinding Complete (A* + CNA)");
            while (true)
            {
                pathResult.Add(new Vector3(ptr.GetNode.getX(), 0, ptr.GetNode.getY()));
                if (ptr.GetNode.getX() == startNode.getX() &&
                    ptr.GetNode.getY() == startNode.getY())
                {
                    return;
                }
                ptr = ptr.ParentNode;
            }
        }

    } while (openList.Count != 0);

    Debug.Log("Can't find path");
}

// 선택된 노드 중 아직 탐색하지 않은 노드를 리스트에 추가합니다.
private void addOpenList(AStarNode ptr)
{
    for (int i = 0; i < ptr.GetNode.getCnn().Count; i++)
    {
        Tuple<PathNode, Vector3> nodeBuffer = ptr.GetNode.getCnn()[i];

        double hScore = Math.Sqrt(
            Math.Pow(targetNode.getX() - nodeBuffer.Item1.getX(), 2) +
            Math.Pow(targetNode.getY() - nodeBuffer.Item1.getY(), 2));

        double gScore = Math.Sqrt(
            Math.Pow(ptr.GetNode.getX() - nodeBuffer.Item1.getX(), 2) +
            Math.Pow(ptr.GetNode.getY() - nodeBuffer.Item1.getY(), 2)) 
            + ptr.GScore;

        double fScore = hScore + gScore;

        if (nodeBuffer.Item1.Status == 0) // When a node doesn't belong any list
        {
            AStarNode newAStarNode = new AStarNode(nodeBuffer.Item1, hScore, gScore, ptr);
            openList.Add(newAStarNode);

            nodeBuffer.Item1.Status = 1;
            nodeBuffer.Item1.AStarNode = newAStarNode;
            nodeBuffer.Item1.FScore = newAStarNode.FScore;
        }
        else if (nodeBuffer.Item1.Status == 1) // When a node belong to open list
        {
            if (fScore < nodeBuffer.Item1.FScore)
            {
                nodeBuffer.Item1.AStarNode.GScore = gScore;
                nodeBuffer.Item1.AStarNode.HScore = hScore;
                nodeBuffer.Item1.AStarNode.FScore = fScore;
                nodeBuffer.Item1.AStarNode.ParentNode = ptr;
            }
        }
    }
}

// 탐색한 노드를 리스트에 추가합니다
private AStarNode addCloseList()
{
    if (openList.Count != 0)
    {
        AStarNode minNode = openList[0];
        for (int i = 0; i < openList.Count; i++)
        {
            if (minNode.FScore > openList[i].FScore)
                minNode = openList[i];
        }

        minNode.GetNode.Status = 2;
        closeList.Add(minNode);
        openList.Remove(minNode);
        return minNode;
    }

    return null;
}
```

---

### 3. MR 내비게이션 시스템 구현 (Unity + MRTK)

![목적지 지정](/assets/images/portfolio_corner_node_algorithm_images/4bda421b-d80c-4fb8-9d40-796b25f37fc8.png)
*목적지 지정*

![경로 안내](/assets/images/portfolio_corner_node_algorithm_images/28.png)
*경로 안내*

| 기술         | 내용                                                         |
| ------------ | ------------------------------------------------------------ |
| 엔진         | Unity                                                        |
| MR Framework | MRTK(Mixed Reality Toolkit)                                  |
| 기능         | 생성된 경로 위에 **3D 안내 오브젝트**를 실시간 표시          |
| 결과         | 사용자 시야에 최단경로를 시각적으로 제공하는 내비게이션 구현 |

#### 핵심 포인트

- Unity 사용으로 **3D 오브젝트 처리 용이**
- MRTK 활용해 **HMD 제스처·공간 인식 자연스럽게 연동**

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