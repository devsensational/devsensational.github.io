---
title: Union-Find
date: 2026-08-06 17:16 +0900
category: [C++]
tags: ["C++", "알고리즘"]
description: 두 그룹이 같은 그룹에 속해 있거나 합쳐야 할 때 유용한 알고리즘
math: true
---

Union-Find를 사용하여 서로 중복되지 않는 부분 집합들을 효율적으로 관리할 수 있습니다(서로소 집합 개념). 핵심은 각 집합의 Root를 이용하여 그룹을 관리하는 것입니다.

기본적으로 다음 3가지 연산으로 작동합니다.

- Initialization (초기화): $N$개의 원소가 각각 자기 자신만을 원소로 갖는 독립된 집합을 형성합니다.
```cpp
int parent[2501]; // 특정 노드의 최상단 노드가 무엇인지 기록 
```
- Find (찾기): 특정 원소 $x$가 속한 집합의 최상위 루트 노드를 반환합니다. `Find(A) == Find(B)`라면 두 원소 $A, B$는 같은 그룹에 속해 있습니다.
- Union (합치기): 두 원소 $a, b$가 속한 두 개의 그룹을 하나로 병합합니다.한쪽 그룹의 루트 노드를 다른 쪽 그룹의 루트 노드의 자식으로 연결합니다.



## 경로 압축 (아주 중요!!!)

트리가 한쪽으로 길게 늘어서는 형태가 되면 Find 탐색 시간이 O(N)까지 늘어날 수 있습니다. 이를 해결하기 위해 경로 압축을 반드시 진행해야 합니다.

Parent를 탐색할 때 루트 노드를 찾아 올라가면서 거쳐간 모든 노드들이 최상위 루트 노드를 직접 가리키도록 부모 배열을 바로바로 갱신합니다.

```cpp
int findNode(int x) 
{
    if (parent[x] == x) return x;
    return parent[x] = find_node(parent[x]);
}
```

재귀를 통해 root(parent 배열이 자신을 가리키면 최상위)까지 이동한 후, 복귀하면서 parent[x]의 값을 root의 인덱스로 수정합니다.

이렇게 하면 줄이 길게 늘어서도 여러번 호출 했을 때 상수시간안에 최상위 노드를 찾을 수 있습니다.

## 활용되는 유형의 문제들
### 크루스칼 알고리즘
[이전 포스트](https://devsensational.github.io/posts/%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98-Kruskal's-Algorithm/)

그래프에서 최소 비용으로 모든 노드를 연결하는 최소 신장 트리(MST)를 구축해야 하는 경우입니다. 이전에도 포스팅 하면서 이 자료구조를 다뤘습니다.

간선들을 가중치 오름차순으로 정렬한 뒤, 간선의 양 끝 정점 $u, v$에 대해 `Find(u) != Find(v)`일 때만 간선을 선택하고 `Union(u, v)`을 수행합니다. (사이클 방지)


### 무방향 그래프 사이클 판별 또는 네트워크 그룹화
[네트워크](https://school.programmers.co.kr/learn/courses/30/lessons/43162)

[표 병합](https://school.programmers.co.kr/learn/courses/30/lessons/150366)

그래프에 간선이 추가되는 과정에서 사이클이 형성되는지 확인해야 하는 유형입니다. 

간선 $(u, v)$를 연결하기 전 `Find(u) == Find(v)` 라면 이미 두 정점이 연결된 상태이므로, 이 간선을 연결하는 순간 사이클이 발생합니다.

특히, 표 병합같은 2차원 공간을 사용하는 문제는 1차원으로 변형하여 일렬로 늘어놓는 방식으로 풀면 더 효율적으로 풀 수 있습니다. 

처음에는 3차원 공간을 만들어서 첫 번째 element가 본인의 위치와 다르면 root로 이동, root가 병합된 cell들의 위치 정보를 갖도록 풀었는데 1차원으로 변형하고 경로 압축을 적용하니 훨씬 간단했습니다.

주의해야 할 점은 병합을 해제해야 할 때 입니다. 특정 집합의 모든 원소의 parent가 자기 자신을 가리키도록 해야 하는데 **병합을 해제하는 과정에서 parent가 바뀌기 때문에 해제할 대상을 모아놓은 후 해제해야 합니다.**

```cpp
    if(cmd[0] == 'U' && cmd[1] == 'N')
    {
        int target = convert(stoi(cmds[1]), stoi(cmds[2]));
        int pa = findParent(target);
        string replace = cache[pa];
        
        // 병합을 해제하면서 부모가 바뀌기 때문에 해제할 대상을 먼저 찾기
        vector<int> unmergeList;
        for(int i = 0; i < 2501; ++i)
        {
            if(findParent(i) == pa) unmergeList.push_back(i);
        }
        
        // 해제
        for(int i: unmergeList)
        {
            parent[i] = i;
            cache[i] = "EMPTY";
        }
        
        cache[target] = replace;
    }
```

이 외에도 역방향 오프라인 쿼리 유형에도 사용한다고 합니다. 