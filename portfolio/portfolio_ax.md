---
layout: page
title: "개발 생산성 향상을 위한 AI 코드 리뷰 자동화 구축"
permalink: /portfolio/portfolio_ax/
---

## 프로젝트 핵심 교훈

- **패턴 탐지에는 우수하나 코드의 맥락과 목적 파악에는 한계가 있음**
  * 코딩 컨벤션 위반이나 널리 알려진 병목 등 정형화된 문제는 훌륭하게 캐치함
  * 초기 버전은 변경된 줄(diff)만 전달했기 때문에, 멤버 선언이나 생명주기 함수처럼 diff 밖에 있는 코드를 보지 못해 리뷰의 정확도가 떨어졌음
  * 이를 헤더/소스를 짝지어 전체 파일을 함께 전달하는 클래스 단위 리뷰로 개선했지만, 다른 클래스와의 상호작용이나 프로젝트 전체 구조, 작성 당시의 기획 의도는 여전히 전달되지 않음
- **의도가 중요한 리뷰의 부재 및 전적인 신뢰의 위험성**
  * 위와 같은 이유로 전체 아키텍처나 기획 의도를 이해해야만 가능한 깊이 있는 조언을 기대하기 어려움
  * 초기 오류 탐지 보조 도구로는 매우 유용하지만, AI 리뷰만 믿고 실제 릴리즈까지 진행하는 것은 아직 리스크가 큼
- **팀원 간 커뮤니케이션의 중요성 재확인**
  * AI에게 맥락을 전달하려면 작성 단계부터 AI 에이전트와 함께 코딩을 진행하거나 상세한 주석으로 의도를 명시해야 함
  * 결국 AI는 리뷰를 돕는 보조 수단일 뿐이며, 복잡한 맥락을 동기화하고 프로젝트의 올바른 방향을 잡기 위해서는 **여전히 팀원 간의 활발한 커뮤니케이션이 가장 중요하다는 것을 재확인함**

---

## 프로젝트 소개

본 프로젝트는 게임 클라이언트 개발 과정에서 발생하는 코드 리뷰의 병목 현상을 해소하고, 일관된 코드 품질을 유지하기 위해 기획된 **AI 기반 자동화 파이프라인**입니다. Docker 환경 위에 구축된 n8n과 로컬 LLM(Ollama)을 연동하여, GitHub Pull Request가 생성될 때마다 AI가 Unreal Engine 5 C++ 코드를 클래스 단위로 분석하고 실무 표준에 맞는 리뷰를 남기는 시스템을 구현했습니다. 특히 외부 LLM API 없이 로컬 LLM으로 동작하도록 구성하여, 소스코드를 제3자 AI 서비스로 전송하지 않고 LLM API 호출 비용도 발생하지 않도록 했습니다.

## 프로젝트 목표

- **리뷰 소요 시간 단축:** PR 리뷰 대기 시간을 최소화하여 개발팀의 전반적인 작업 속도(Velocity) 및 이터레이션 속도 향상
- **코드 품질 및 안정성 표준화:** 사전에 정의된 엄격한 시스템 프롬프트를 통해 버그 위험, 생명주기(Lifecycle) 오류, 성능 저하 요인 등을 일관되게 탐지
- **보안 및 비용 효율성 확보:** Docker와 로컬 LLM을 활용한 셀프 호스팅 환경 구축 경험

## 시스템 흐름

![image.png](/assets/images/portfolio_ax_images/workflow.png)

- **Github Trigger:** 대상 저장소에서 Pull Request 이벤트(생성, 업데이트 등)가 발생하면 Webhook을 통해 자동으로 워크플로우가 시작됩니다.
- **Github File Request (PR 대상 파일 조회):** GitHub API(`{% raw %}{{ $json.body.pull_request.url + "/files" }}{% endraw %}`)를 호출하여 PR에 포함된 변경 파일 목록과 각 파일의 diff(patch)를 가져옵니다.
- **File Filtering (필터링 및 헤더/소스 매칭):** 변경된 파일 중 `.h`/`.cpp` (C++) 파일만 추출하고, 같은 클래스의 헤더와 소스를 하나의 리뷰 단위로 묶습니다. Unreal Engine 모듈 구조(`Public`/`Private`/`Classes`)를 고려해 경로를 정규화하여, 서로 다른 폴더에 있는 헤더와 소스도 짝지을 수 있도록 했습니다. 한쪽 파일만 변경된 경우에는 저장소에서 짝이 되는 파일의 경로 후보를 생성합니다.
- **Build Fetch List (조회 목록 생성):** 각 리뷰 단위에서 전체 내용이 필요한 파일(변경된 파일 + 짝 파일 후보)을 개별 요청 목록으로 펼칩니다.
- **Fetch Full File (전체 파일 조회):** PR head 커밋 기준으로 각 파일의 전체 소스를 가져옵니다. diff만으로는 보이지 않는 멤버 선언, 생명주기 함수, 호출 맥락까지 LLM이 참고할 수 있도록 하기 위함입니다. 존재하지 않는 후보 경로(404)는 오류 없이 건너뜁니다.
- **Build Review Input (리뷰 입력 구성):** 전체 파일에 줄 번호를 붙이고, diff를 파싱해 이번 PR에서 추가·수정된 줄은 `+`로 표시하며, 삭제된 줄은 원래 위치와 함께 별도로 정리합니다. diff와 전체 파일을 중복으로 넣지 않아 토큰 사용을 줄였고, 파일이 지나치게 길면 변경된 줄 주변만 남겨 컨텍스트 한도를 넘지 않도록 했습니다. PR에서 변경되지 않은 짝 파일은 '참고용'으로 함께 전달합니다.
- **LLM Request (로컬 LLM 분석):** 클래스 단위로 구성된 리뷰 입력을 Docker 내부의 Ollama(`gpt-oss:20b`) API로 POST 요청합니다. 리뷰 기준을 담은 system 프롬프트와 코드를 담은 user 메시지를 분리했고, 추론 강도(`think: medium`)와 컨텍스트 크기(`num_ctx: 32768`)를 지정했습니다. 프롬프트는 C++/Unreal Engine 5에 특화되어 다음 7가지 기준을 우선순위대로 분석하도록 지시합니다.
  1. 크래시/미정의 동작 위험 (null 역참조, 컨테이너 범위 초과 등)
  2. UObject 수명 관리 및 GC (`UPROPERTY`, `TObjectPtr` 누락 등)
  3. 게임플레이 프레임워크 생명주기 (`Super::` 호출 누락 등)
  4. 네트워크 리플리케이션 (`DOREPLIFETIME` 등록 누락 등)
  5. 유지보수성 및 책임 분리
  6. 성능 (Tick 내부의 고비용 호출 등)
  7. Epic 코딩 표준
  
  헤더와 소스가 함께 주어지면 선언·정의 간 일관성도 별도 항목으로 점검합니다.
- **Create a review (리뷰 등록):** 분석 결과를 리뷰 대상 클래스명 및 파일 목록과 함께 PR에 리뷰 코멘트로 등록합니다. 변경된 클래스마다 별도의 리뷰가 작성됩니다.

### API 요청을 위한 JSON 및 프롬프트 보기

<details markdown="1"> <summary><code>Ollama 요청 JSON + 시스템 프롬프트</code></summary>

{% raw %}

```
{{
{
  model: "gpt-oss:20b",
  stream: false,
  think: "medium",
  options: {
    num_ctx: 32768
  },
  messages: [
    {
      role: "system",
      content: `Unreal Engine 5 C++ code review task.

Role:
- You are a senior Unreal Engine 5 C++ engineer reviewing a pull request.
- Review using practical UE5 and modern C++ standards, plus the Epic Games C++ Coding Standard.
- Focus on correctness, crash safety, UObject lifetime/GC, gameplay framework lifecycle, maintainability, and performance.
- Do not change the original intent of the code.

Input format:
- One review unit = one class: its header (.h) and source (.cpp).
- Files are shown in full with line numbers, one line per row: "<marker> <line number> | <code>".
- Marker "+" means the line was added or modified in this PR. A blank marker means the line already existed.
- "삭제된 줄" lists lines removed in this PR and the line they used to follow.
- Files labeled "참고용" were not changed in this PR. They are context only.
- If a file could not be loaded in full, only its unified diff is shown ("+" added, "-" removed, " " context).
- Very long files may have omitted ranges marked "생략".

Review scope:
- Review the changed lines ("+" lines and deleted lines) first.
- Use the rest of the file to understand types, members, lifecycle, and call sites of the changed code.
- Report problems in unchanged code only when the change depends on them or interacts with them, and mark them "(기존 코드)".
- Do not review "참고용" files on their own. Use them only to check the changed code (declaration/definition consistency, UPROPERTY on members, etc.).
- If the counterpart file is missing, say what cannot be verified.

Strict output rules:
- Respond in Korean.
- Code, identifiers, macros, and Unreal/C++ technical terms (UPROPERTY, TObjectPtr, BeginPlay, etc.) stay in their original form.
- No greetings, introductions, self-introduction, roleplay, compliments, or filler.
- Keep it concise and practical like a real code review.
- Do not make assumptions about code that was not provided.
- If uncertain, explicitly say "가능성이 있습니다".
- Do not invent problems. If the change is trivial (comments, whitespace, empty template code) or has no real issue, say so briefly.

Review priority:
1. Crash / undefined behavior risks
2. UObject lifetime and garbage collection issues
3. Gameplay framework lifecycle issues
4. Networking / replication correctness
5. Maintainability and responsibility separation
6. Performance (only when there is a realistic cost)
7. Coding standard and style

Always check:

[Crash / UB]
- Null dereference of UObject pointers, components, GetWorld(), GetOwner(), Cast results
- IsValid() vs plain nullptr checks for objects that may be pending kill
- TArray / TMap access without IsValidIndex / Contains / Find checks
- Uninitialized member variables (especially raw pointers, bools, numeric types)
- Misuse of check / ensure / verify (check on recoverable conditions, side effects inside check)
- Division by zero, integer overflow, signed/unsigned mismatch

[UObject lifetime / GC]
- UObject pointer members without UPROPERTY (can be garbage collected and become dangling)
- UE5 style: TObjectPtr for UObject member pointers in headers
- TWeakObjectPtr for non-owning references, TSoftObjectPtr / TSoftClassPtr for assets that should not be hard-loaded
- UObjects held by non-UObject classes without FGCObject or TStrongObjectPtr
- NewObject outer choice, AddToRoot / RemoveFromRoot misuse
- Raw "this" captured in lambdas, timers, async tasks (prefer CreateWeakLambda, AddUObject, weak pointers)

[Gameplay framework lifecycle]
- CreateDefaultSubobject only in constructor; no world/gameplay access in constructor
- Correct use of Constructor / PostInitializeComponents / BeginPlay / EndPlay / Tick
- Missing Super:: calls in overridden virtual functions (BeginPlay, EndPlay, Tick, PostInitializeComponents, GetLifetimeReplicatedProps, SetupPlayerInputComponent, etc.)
- Delegates, timers, and input bindings not cleaned up in EndPlay / BeginDestroy
- AddDynamic target functions must be UFUNCTION; duplicate bindings
- Enhanced Input usage (UE5): mapping context added/removed properly

[Networking / replication]
- Replicated / ReplicatedUsing properties registered with DOREPLIFETIME in GetLifetimeReplicatedProps
- OnRep functions as UFUNCTION
- HasAuthority / role checks before authority-only logic
- Server RPC validation, Reliable RPC overuse (especially from Tick)

[Performance]
- Tick enabled when not needed (PrimaryActorTick.bCanEverTick, component tick)
- GetAllActorsOfClass, FindComponentByClass, GetComponents, Cast, string lookups inside Tick or hot paths
- Large containers or FString passed by value instead of const reference
- Missing Reserve for known-size containers, unnecessary copies in range-for (use const auto&)
- FName vs FString vs FText choice, logging inside Tick

[Unreal C++ conventions]
- Type prefixes: A (Actor), U (UObject), F (struct/plain), E (enum), I (interface), T (template), b (bool)
- UCLASS / USTRUCT / UENUM / GENERATED_BODY correctness; UENUM as "enum class : uint8"
- UPROPERTY / UFUNCTION specifiers: EditAnywhere vs EditDefaultsOnly vs VisibleAnywhere, BlueprintReadOnly vs BlueprintReadWrite, Category set
- Overexposed public members (prefer private/protected + accessor or meta=(AllowPrivateAccess="true"))
- Header hygiene: forward declarations instead of heavy includes, IWYU, .generated.h as the last include
- MODULENAME_API for classes/functions used from other modules
- TEXT() for string literals, const correctness, override keyword, auto overuse
- Magic numbers (prefer UPROPERTY config values or constexpr), duplicate code, long functions, too many responsibilities

Severity levels:
- Critical: crash, undefined behavior, GC/dangling pointer, or incorrect behavior risk
- Warning: lifecycle, replication, maintainability, structure, or realistic performance issue
- Suggestion: recommended improvement
- Style: naming, formatting, or coding standard issue

Output format:

## 전체 평가
- Summarize the overall state in 2~4 sentences
- Mention the highest priority issue first

## 주요 문제점

### [Critical|Warning|Suggestion|Style] 제목
- 위치: file name and line number from the listing (approximate line from the hunk header if only a diff is shown)
- 설명:
- 이유:
- 개선안:
- 예시: short C++ code block, only when it helps

(repeat as needed, ordered by severity)

## 헤더/소스 일관성
- Only when both header and source are provided (changed or 참고용)
- Declaration/definition mismatch, specifier mismatch, missing implementation, unused declarations

## 잘된 점
- Only include if genuinely meaningful

## 개선 우선순위
1.
2.
3.

Additional rules:
- Clearly distinguish Epic coding standard / team convention issues from objective problems.
- Only mention performance issues when there is a realistic cost.
- Maintain the exact output structure. Omit a section only when it explicitly says it is optional.
- Do not output text outside the review sections.
- Start directly with the review output.`
    },
    {
      role: "user",
      content: $json.reviewInput
    }
  ]
}
}}

```

{% endraw %}

</details>

## 결과물

- **n8n 자동화 워크플로우 연동:** GitHub - n8n - Ollama(`gpt-oss:20b`)를 잇는 무인 파이프라인 구축 완료
- **클래스 단위 전체 맥락 리뷰:**
    - 헤더(`.h`)와 소스(`.cpp`)를 자동으로 짝지어 클래스 하나를 한 번에 리뷰하도록 구성
    - diff 조각이 아닌 PR 브랜치 기준 전체 파일을 전달하고, 변경된 줄만 표시하여 맥락은 유지하면서 리뷰 범위는 명확히 한정
    - PR에서 변경되지 않은 짝 파일도 저장소에서 찾아 참고용으로 함께 전달하여, 멤버 선언 누락이나 선언·정의 불일치까지 검출 가능
- **Unreal Engine 5 특화 AI 시스템 프롬프트 엔지니어링:**
    - 단순 문법 검사가 아닌 실무 표준에 맞춘 7가지 핵심 리뷰 기준 확립
        - 크래시/미정의 동작 위험
        - UObject 수명 관리 및 GC
        - 게임플레이 프레임워크 생명주기
        - 네트워크 리플리케이션
        - 유지보수성
        - 성능
        - Epic 코딩 표준
    - 문제가 없는 변경에 대해 억지로 지적을 만들어내지 않도록 제한하고, 변경과 무관한 기존 코드는 리뷰 대상에서 제외하여 노이즈 최소화
    - 불필요한 인사말이나 부연 설명을 배제하고, 아래 구조로만 출력하도록 강제하여 가독성 극대화
    
    ```
    ## 전체 평가
    ## 주요 문제점
    ## 헤더/소스 일관성
    ## 잘된 점
    ## 개선 우선순위
    ```

### 실제 결과물 예시 보기

![스크린샷 2026-05-14 153452.png](/assets/images/portfolio_ax_images/review_example.png)

## 성과 및 기대 효과

- **리뷰 1차 응답의 자동화:** PR을 올리기만 하면 사람의 개입 없이 변경된 클래스마다 리뷰 코멘트가 자동으로 등록되는 흐름을 구축하여, 리뷰어 배정을 기다리지 않고 즉시 1차 피드백을 받을 수 있게 함
- **휴먼 에러 사전 탐지:** `Tick` 내부의 `GetAllActorsOfClass` 같은 고비용 호출, `UPROPERTY` 누락으로 인한 GC 문제, 오버라이드 함수의 `Super::` 호출 누락 등 개발자가 놓치기 쉬운 UE5 특유의 결함을 사람이 리뷰하기 전에 1차로 걸러낼 수 있음
- **리뷰어 부담 분산:** 단순 컨벤션이나 기본적인 결함은 AI가 먼저 지적하므로, 사람 리뷰어는 설계와 기획 의도처럼 AI가 판단하기 어려운 부분에 집중할 수 있음
- **비용 없는 운영:** 로컬 LLM으로 동작하므로 PR 수나 코드 양이 늘어도 LLM API 비용이 추가로 발생하지 않음

## 한계 및 향후 개선 과제

- **트리거 조건 세분화:** 현재는 PR의 모든 이벤트에 반응하므로, PR을 닫거나 라벨을 붙일 때도 리뷰가 실행될 수 있음. 생성·업데이트·재오픈 이벤트만 처리하도록 필터를 추가할 예정
- **증분 리뷰:** PR이 업데이트될 때마다 전체 파일을 다시 리뷰하여 코멘트가 중복으로 쌓임. 직전 리뷰 이후 새로 바뀐 커밋만 리뷰하도록 개선이 필요
- **대규모 PR 대응:** GitHub 파일 목록 API의 페이지 제한(기본 30개)으로 인해, 변경 파일이 많은 PR은 일부만 리뷰될 수 있음. 페이지네이션 처리가 필요
- **클래스 간 맥락:** 리뷰 단위가 클래스 하나이므로, 여러 클래스에 걸친 상호작용이나 아키텍처 수준의 문제는 탐지하기 어려움

<br><br>

<div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
  <a href="/portfolio/" style="display: inline-block; padding: 14px 28px; font-size: 1.05rem; font-weight: 600; color: #495057; background-color: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 8px; text-decoration: none; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease-in-out;">
    <i class="fas fa-arrow-left" style="margin-right: 8px; color: #6c757d;"></i> 포트폴리오 리스트로 돌아가기
  </a>
</div>