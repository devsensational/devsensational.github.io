---
layout: page
title: "개발 생산성 향상을 위한 AI 코드 리뷰 자동화 구축"
permalink: /portfolio/portfolio_ax/
---

## 프로젝트 핵심 교훈

- **패턴 탐지에는 우수하나 코드의 맥락과 목적 파악에는 한계가 있음**
  * 코딩 컨벤션 위반이나 널리 알려진 병목 등 정형화된 문제는 훌륭하게 캐치함
  * 하지만 자동화 파이프라인을 통해 전체 파일을 처리하는 것이 아닌, 업로드 된 코드 파일을 각각 처리하기 때문에 작성 당시의 전체 맥락과 비즈니스 목적이 소실됨
- **의도가 중요한 리뷰의 부재 및 전적인 신뢰의 위험성**
  * 위와 같은 이유로 전체 아키텍처나 기획 의도를 이해해야만 가능한 깊이 있는 조언을 기대하기 어려움
  * 초기 오류 탐지 보조 도구로는 매우 유용하지만, AI 리뷰만 믿고 실제 릴리즈까지 진행하는 것은 아직 리스크가 큼
- **팀원 간 커뮤니케이션의 중요성 재확인**
  * AI에게 맥락을 전달하려면 작성 단계부터 AI 에이전트와 함께 코딩을 진행하거나 상세한 주석으로 의도를 명시해야 함
  * 결국 AI는 리뷰를 돕는 보조 수단일 뿐이며, 복잡한 맥락을 동기화하고 프로젝트의 올바른 방향을 잡기 위해서는 **여전히 팀원 간의 활발한 커뮤니케이션이 가장 중요하다는 것을 재확인함**

---

## 프로젝트 소개

본 프로젝트는 게임 클라이언트 개발 과정에서 발생하는 코드 리뷰의 병목 현상을 해소하고, 일관된 코드 품질을 유지하기 위해 기획된 **AI 기반 자동화 파이프라인**입니다. Docker 환경 위에 구축된 n8n과 로컬 LLM(Ollama)을 연동하여, GitHub Pull Request가 생성될 때마다 AI가 자동으로 코드를 분석하고 실무 표준에 맞는 리뷰를 남기는 시스템을 구현했습니다. 특히 외부 API 의존 없이 로컬 환경에서 동작하도록 구성하여 소스코드 유출에 대한 보안성을 높이고 API 호출 비용을 제거했습니다.

## 프로젝트 목표

- **리뷰 소요 시간 단축:** PR 리뷰 대기 시간을 최소화하여 개발팀의 전반적인 작업 속도(Velocity) 및 이터레이션 속도 향상
- **코드 품질 및 안정성 표준화:** 사전에 정의된 엄격한 시스템 프롬프트를 통해 버그 위험, 생명주기(Lifecycle) 오류, 성능 저하 요인 등을 일관되게 탐지
- **보안 및 비용 효율성 확보:** Docker 및 로컬 LLM 아키텍처를 통한 On-Premises 구축 경험

## 시스템 흐름

![image.png](/assets/images/portfolio_ax_images/image.png)

- **GitHub Trigger:** 대상 저장소에 새로운 Pull Request가 생성되거나 업데이트될 때 Webhook을 통해 자동으로 워크플로우가 시작됩니다.
- **HTTP Request (PR 대상 파일 조회):** GitHub API(`{% raw %}{{ $json.body.pull_request.url + "/files" }}{% endraw %}`)를 호출하여 PR에 포함된 변경된 파일 목록을 가져옵니다.
- **Code in JavaScript (필터링):** 변경된 파일 중 게임 클라이언트 스크립트에 해당하는 `.cs` (C#) 파일만 추출하여 다음 노드로 전달합니다.
- **HTTP Request (로컬 LLM 분석):** 필터링된 코드 패치를 Docker 내부의 Ollama(`qwen3.5:9b`) API로 POST 요청합니다. 이때 Unity/C# 환경에 특화된 프롬프트를 적용하여 유지보수성, 성능, 아키텍처 문제를 집중적으로 분석하도록 지시합니다.

### API 요청을 위한 JSON 및 프롬프트 보기

{% raw %}
```
{{
{
  model: "qwen3.5:9b",
  stream: false,
  messages: [
    {
      role: "system",
      content: `Unity C# code review task.

Role:
- Review Unity C# scripts using practical Unity and C# development standards.
- Focus on maintainability, stability, structure, readability, and performance.
- Do not change the original intent of the code.

Strict output rules:
- Respond in Korean only.
- Do not use English in the response.
- Do not include greetings, introductions, or self-introduction.
- Do not roleplay as an assistant.
- Do not add unnecessary compliments or filler text.
- Keep responses concise and practical like a real code review.
- Do not make assumptions about code that was not provided.
- If uncertain, explicitly say "가능성이 있습니다".

Review priority:
1. Bug risks
2. NullReferenceException risks
3. Unity lifecycle issues
4. Maintainability
5. Structure and responsibility separation
6. Performance
7. Style and conventions

Always check:
- Proper use of SerializeField
- Overuse of public fields
- Unnecessary operations inside Update
- Repeated GetComponent/Find calls
- Event subscription/unsubscription issues
- Inspector assignment risks
- Magic numbers
- Duplicate code
- Long methods
- Excessive class responsibilities
- Naming conventions
- Null safety
- Collection access safety
- Coroutine safety

Severity levels:
- Critical: Crash or incorrect behavior risk
- Warning: Maintainability, structure, or performance issue
- Suggestion: Recommended improvement
- Style: Naming, formatting, or convention issue

Output format:

## 전체 평가
- Summarize the overall state in 2~4 sentences
- Mention the highest priority issue first

## 주요 문제점

### [Critical|Warning|Suggestion|Style] 제목
- 설명:
- 이유:
- 개선안:
- 예시:

(repeat as needed)

## 잘된 점
- Only include if genuinely meaningful

## 개선 우선순위
1.
2.
3.

Additional rules:
- Consider Unity Inspector assignment behavior.
- Prefer [SerializeField] for private fields exposed to Inspector.
- Only mention performance issues when there is a realistic cost.
- Clearly distinguish team convention issues from objective problems.

Important:
- Maintain the exact output structure.
- Do not output unnecessary text outside the review sections.
- Do not generate greetings or conversational filler.
- Do not explain what you are going to do.
- Start directly with the review output.

Now review the provided Unity C# code.

파일명:
${$json.filename}

Patch:
${$json.patch}`
    }
  ]
}
}}
```
{% endraw %}

## 결과물

- **n8n 자동화 워크플로우 연동:** GitHub - n8n - Ollama를 잇는 무인 파이프라인 구축 완료
- **게임 개발 특화 AI 시스템 프롬프트 엔지니어링:**
    - 단순 문법 검사가 아닌 실무 표준에 맞춘 7가지 핵심 리뷰 기준 확립 (버그 위험도, NullReferenceException 위험, 성능, 유지보수성 등)
    - 불필요한 인사말이나 부연 설명을 배제하고, 아래 구조로만 출력하도록 강제하여 가독성 극대화
    
    ```
    ## 전체 평가
    ## 주요 문제점
    ## 잘된 점
    ## 개선 우선순위
    ```

### 실제 결과물 예시 보기

![스크린샷 2026-05-14 153452.png](/assets/images/portfolio_ax_images/image2.png)

## 성과

- **휴먼 에러 사전 차단:** 개발자가 놓치기 쉬운 `Update` 문 내부의 무거운 연산, 불필요한 `GetComponent` 호출, 코루틴 안전성 등의 이슈를 AI가 1차적으로 필터링하여 런타임 크래시 발생률 감소
- **개발자 피로도 감소:** 시니어 개발자가 단순 컨벤션이나 기본적인 구조적 결함을 리뷰하는 데 사용하는 시간을 대폭 절감하여, 핵심 시스템 기획 및 아키텍처 설계에 집중할 수 있는 환경 조성

<br><br>

<div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
  <a href="/portfolio/" style="display: inline-block; padding: 14px 28px; font-size: 1.05rem; font-weight: 600; color: #495057; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 8px; text-decoration: none; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease-in-out;">
    <i class="fas fa-arrow-left" style="margin-right: 8px; color: #6c757d;"></i> 포트폴리오 리스트로 돌아가기
  </a>
</div>