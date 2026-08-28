---
icon: fas fa-briefcase
order: 4
title: PORTFOLIO
---

## 기본기에 충실하고, 성장을 즐기는 신입 개발자입니다!


>- 절차적 맵 생성, 매치메이킹, UI 등 프로젝트를 통한 다양한 분야 구현 경험 (C++, C#)
>- 10회 이상의 팀 리더 경험과 시행착오로 길러진 커뮤니케이션 스킬
>- 연구 과제 최적화 경험 및 논문 작성 경험 (SCI-E 저널 1저자)
>- AI/AX 기반 자동화를 통해 개발 생산성과 반복 업무 효율을 극대화하는 개발자

---

<style>
  /* 카드 전체 컨테이너 */
  .pf-card {
    display: flex;
    align-items: center; /* stretch에서 center로 변경: 텍스트 길이에 의해 이미지가 기형적으로 길어지는 현상 방지 */
    border-radius: 12px;
    border: 1px solid var(--card-border-color, rgba(128, 128, 128, 0.15));
    background-color: transparent;
    overflow: hidden;
    margin-bottom: 2rem;
    position: relative;
    transition: background-color 0.3s ease;
  }

  /* 마우스 호버(Hover) 시 연한 회색으로 서서히 덮이는 효과 */
  .pf-card:hover {
    background-color: var(--card-hover-bg, rgba(128, 128, 128, 0.12)); 
  }

  /* 왼쪽 이미지 영역 */
  .pf-img-area {
    flex: 0 0 30%; 
    max-width: 250px;
    margin: 0; 
    padding: 0; 
    border-right: 1px solid var(--card-border-color, rgba(128, 128, 128, 0.15)); 
  }

  .pf-img-area img {
    width: 100%;
    height: 100%;
    aspect-ratio: 4 / 3; /* 이미지 영역을 4:3 비율로 강제 고정 */
    object-fit: cover; /* 비율을 유지하면서 꽉 채우고, 넘치는 부분은 자동 크롭 */
    object-position: center; /* 크롭될 때 상하좌우 치우치지 않고 정중앙을 기준으로 자름 */
    display: block;
  }

  /* 오른쪽 텍스트 영역 */
  .pf-text-area {
    flex: 1;
    padding: 1.8rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .pf-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-top: 0;
    margin-bottom: 0.6rem;
    color: var(--heading-color, inherit);
  }

  .pf-desc {
    margin: 0;
    font-size: 0.95rem;
    color: var(--text-muted-color, #6c757d);
    line-height: 1.6;
  }

  /* 카드 전체를 클릭 가능하게 만드는 투명 링크 */
  .pf-click-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 10;
    border: none !important; /* Chirpy 테마의 오렌지색 밑줄 효과 강제 제거 */
    text-decoration: none !important; 
  }
  
  /* 마우스를 올렸을 때도 오렌지색 선이 생기지 않도록 차단 */
  .pf-click-overlay:hover {
    border: none !important;
  }
</style>

<!-- 포트폴리오 아이템 1 -->
<div class="pf-card">
  <a href="/portfolio/portfolio_project_arc/" class="pf-click-overlay"></a>
  <div class="pf-img-area">
    <img src="/assets/images/portfolio_project_arc_images/image.png" alt="Project Arc thumbnail">
  </div>
  <div class="pf-text-area">
    <h3 class="pf-title">Project Arc</h3>
    <p class="pf-desc">Unreal 5, 절차적 맵 생성, 네트워크 동기화 문제 해결 등</p>
  </div>
</div>

<!-- 포트폴리오 아이템 2 -->
<div class="pf-card">
  <a href="/portfolio/portfolio_corner_node_algorithm/" class="pf-click-overlay"></a>
  <div class="pf-img-area">
    <img src="/assets/images/portfolio_corner_node_algorithm_images/28.png" alt="MR 환경 내비게이션 썸네일">
  </div>
  <div class="pf-text-area">
    <h3 class="pf-title">MR 환경 내비게이션 개발 프로젝트</h3>
    <p class="pf-desc">대학 연구 과제, SCI-E 논문 1저자 등재, Unity, Pathfinding 최적화 등</p>
  </div>
</div>

<!-- 포트폴리오 아이템 3 -->
<div class="pf-card">
  <a href="/portfolio/portfolio_ax/" class="pf-click-overlay"></a>
  <div class="pf-img-area">
    <img src="/assets/images/portfolio_ax_images/image.png" alt="AI 코드 리뷰 썸네일">
  </div>
  <div class="pf-text-area">
    <h3 class="pf-title">개발 생산성 향상을 위한 AI 코드 리뷰 자동화 구축</h3>
    <p class="pf-desc">AX, n8n, Ollama, Docker, 커뮤니케이션의 중요성 등</p>
  </div>
</div>