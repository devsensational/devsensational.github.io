---
title: "[UE5] Gameplay Ability System"
description: "Gameplay Ability System은 언리얼에서 제공하는 범용적인 스킬 시스템 프레임워크입니다. "
date: 2025-09-03T11:18:02.407Z
categories: [UE5]
tags: ["gas","ue5"]
---
이번 포스트에서는 프로젝트에 Gameplay Ability System(이하 GAS)를 적용하기 전에 한 번 정리를 하려고 합니다. 

---

# GAS란 무엇인가?

Gameplay Ability System은 언리얼에서 제공하는 범용적인 스킬 시스템 프레임워크입니다. 단순히 스킬만 다루는 게 아니라, 능력(Ability), 효과(Effect), 속성(Attribute), 태그(Tag) 등을 체계적으로 관리합니다. RPG, FPS, MOBA 등 다양한 장르에서 복잡한 전투 시스템을 만들 때 유용합니다.

### GAS의 주요 개념
- Attribute (속성)
  - 캐릭터의 체력, 마나, 공격력, 이동 속도 같은 값들을 말합니다.
  - UAttributeSet 클래스에 정의합니다.
  - 보통 GameplayEffect를 통해 변동됩니다.
- Gameplay Effect (GE)
  - 스탯 변경, 버프/디버프 같은 효과를 정의합니다.
  - 예: 체력을 50 감소시키는 효과, 이동속도를 20% 증가시키는 효과
  - 지속형/즉발형/주기적(DoT/HoT) 모두 지원합니다.
- Gameplay Ability (GA)
  - 실제로 실행되는 "능력"입니다.
  - 예: "파이어볼 쏘기", "대시하기"
  - Input(키 입력)과 연결해서 사용합니다.
  - Ability 실행 시 필요한 비용(마나, 쿨다운)과 조건(태그, 상태)을 설정할 수 있습니다.
- Gameplay Tag
  - "Stun", "Burning", "Skill.Fireball" 같은 식별자 태그입니다.
  - 조건 체크, 쿨다운, 무효화, 상태 구분 등에 사용됩니다.
- ASC (Ability System Component)
  - GAS의 핵심 매니저 역할을 하는 컴포넌트입니다.
  - 캐릭터에 붙어서 Ability, Effect, Attribute를 관리합니다.
  
  
### GAS의 동작 흐름
  
**1. ASC 부착:** 캐릭터에 UAbilitySystemComponent를 붙여서 GAS 사용 준비.
**2. AttributeSet 등록:** HP, MP, 공격력 등 필요한 속성을 정의.
**3. Gameplay Ability 등록:** 캐릭터가 사용할 수 있는 스킬들을 Ability 클래스로 구현.
**4. Input 바인딩:** 플레이어 입력 → ASC → Ability 실행.
**5. Gameplay Effect 적용:** Ability 실행 시 Effect를 ASC에 적용해서 스탯 변경, 상태 이상 부여.

---

제가 생각하는 GAS의 최대 장점은 확장성과 일관성 있는 구조인 것 같습니다. 이전에 GAS를 사용하지 않고 프로젝트를 진행했을 때에는 미숙한 구조 설계 때문에 애를 먹었는데, GAS는 엔진 개발자 분들에 의해 어느정도 완성된 설계이기 때문에 비슷한 경험을 할 확률이 감소할 것입니다. 몰론 직접 적용해보면서 다른 문제가 발생할 수도 있지만 말이죠.

또한, 예측 입력을 지원하는 것도 장점입니다. 이전 토이 프로젝트에서는 발사 요청 -> 서버에서 발사 로직 실행 -> 클라이언트에 결과 전달 같은 방식으로 진행 됐기 때문에 반응성을 포기할 것인지, 안정성을 포기할지 선택했어야 했는데 예측 입력이 적용되어 있기 때문에 고민할 필요가 없습니다.