---
title: "[알고리즘] Kruskal's Algorithm"
description: "크루스칼 알고리즘은 최소 신장 트리(Minimum Spanning Tree, MST)를 구하는 대표적인 그리디 알고리즘입니다."
date: 2025-09-04T11:16:13.569Z
tags: ["C++","알고리즘"]
thumbnail: /assets/images/old/29963d03-bad0-4c9e-869f-90d752a50a10-image.png
categories: [C++]
---
## 개념
크루스칼 알고리즘은 **최소 신장 트리(Minimum Spanning Tree, MST)**를 구하는 대표적인 그리디 알고리즘입니다.

### 최소 신장 트리란?
- 그래프의 모든 정점을 연결하는 부분 그래프
- 사이클이 없음 (트리 구조)
- 간선의 가중치 합이 최소

더 자세한 내용은 아래 블로그에서도 보실 수 있습니다.
https://wisdom-and-record.tistory.com/124

## 알고리즘 동작 원리
1. 모든 간선을 가중치 기준으로 **오름차순 정렬**
2. 가중치가 작은 간선부터 하나씩 선택
3. **사이클을 형성하지 않는** 간선만 MST에 추가
4. 정점 수 - 1개의 간선이 선택될 때까지 반복

## 시간복잡도
- **O(E log E)**: 간선 정렬에 필요한 시간
- Union-Find 연산: 거의 O(1) (아커만 함수의 역함수)
- **전체: O(E log E)**

## 공간복잡도
- **O(V)**: Union-Find 자료구조
- **O(E)**: 간선 저장

## 특징 및 장단점

### 장점
- 구현이 비교적 간단
- 희소 그래프(간선이 적은 그래프)에서 효율적
- 그리디 알고리즘의 정확성이 증명됨

### 단점
- 밀집 그래프에서는 프림 알고리즘이 더 효율적일 수 있음
- 모든 간선을 정렬해야 함

## 관련 문제
### 프로그래머스 "섬 연결하기" 문제
![](/assets/images/old/29963d03-bad0-4c9e-869f-90d752a50a10-image.png)

https://school.programmers.co.kr/learn/courses/30/lessons/42861

## 소스코드 

```cpp
#include <string>
#include <vector>
#include <algorithm>

using namespace std;

struct DisjointSet
{
    vector<int> parent;
    DisjointSet(int n): parent(n)
    {
        for(int i = 0; i < n; ++i) parent[i] = i;
    }
    
    int find(int x)
    {
        if(parent[x] == x) return x;
        return parent[x] = find(parent[x]);
    }
    
    bool unite(int a, int b)
    {
        a = find(a);
        b = find(b);
        if(a == b) return false;
        parent[b] = a;
        return true;
    }
};

int solution(int n, vector<vector<int>> costs) 
{
    int answer = 0;
    sort(costs.begin(), costs.end(), [](auto& a, auto& b){ return a[2] < b[2]; });
    DisjointSet dsu(n);
    
    for(auto& edge: costs)
    {
        int u = edge[0];
        int v = edge[1];
        int w = edge[2];
        if(dsu.unite(u, v))
        {
            answer += w;
        }
    }
    return answer;
}
```