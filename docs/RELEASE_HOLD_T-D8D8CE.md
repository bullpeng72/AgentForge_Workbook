# release_hold — AgentForge (T-D8D8CE)

## 무엇을 릴리스하는가

v0-v5 전 버전(Spec Interpreter → Team Designer → Code Generator → Verifier → Pool/Composer
→ Web UI)이 구현·실측 완료됐다. 태그: `v0-baseline` · `v2-real-codegen` · `v3-self-eval` ·
`team-ci-ready` · `phase6-skills` · `v4-pool-compose` · `v5-webui`.

## 실측 게이트 상태 (results/gate_run_8.json, 8건 골든셋)

`agent-eval gate results/gate_run_8.json --tcr 85 --decision-log .aoo/decisions.jsonl`
(gate_run id `53fa301d9e69`, `--accuracy 70`로 먼저 잘못 실행한 `c15544bd4804`는 원장에
남겨두고 rejected로 종결 — 이 파이프라인은 task_type="planning"이라 accuracy_score가
애초에 채워지지 않는다, LIMITS 밖의 단순 CLI 플래그 실수):

| Gate | 점수 | 상태 |
|---|---|---|
| A 목표달성 | 0.9082 | pass |
| B 행동무결성 | 0.9375 | pass |
| C 신뢰성 | 1.0 | pass |
| D 성능계약 | 0.6347 | **warn**(0.7 미달) |
| E 보안경계 | 1.0 | pass |
| F 멀티에이전트조율 | 0.687 | **warn**(0.7 미달) |
| G 관측성 | 1.0 | pass |
| **overall** | **0.8811** | pass (TCR 100% ≥ 85%) |

## 알려진 갭 (숨기지 않고 그대로 명시)

- **Gate D**(성능계약): p95 지연이 임계값 근처(LIMITS 없음, ADR §7 트레이드오프에서 예견됨 —
  Tier1 3개 컴포넌트가 전부 클라우드 호출). 두 차례(Part VII Ch30·Part IX 재시도) 수정
  시도가 있었으나 `agent-eval experiment`가 정량적으로 반증 — 점수 역산하지 않고 그대로
  둠(feedback-established 원칙).
- **Gate F**(멀티에이전트조율): coordination_score 0.687 — 별도 하네스(`gate_f_run.json`)
  실측, 구조적 원인 조사는 Part VIII에서 진행.
- **LIMITS L4**(Part X): Pool Composer의 자동 어댑터가 GPT-5의 역할명 변동성 앞에서 자주
  `flag_for_human`으로 샌다 — 설계상 의도된 안전장치, 결함 아님.
- **LIMITS L5**(신규, Part XII 착수 시 발견): SPEC §9가 계획한 v4 10건 골든셋(재사용
  5+신규 5)이 실제로 만들어지지 않았다 — Pool 재사용 메커니즘은 3건짜리 실측 하네스로
  "작동함"은 증명됐지만(`v4-pool-compose`, `reuse_exact` 실제 발동 확인), Gate 점수 기준
  회귀 테스트 커버리지는 없다.

## 결정

이 저장소는 실습 교재용 예제이지 상품이 아니다(SPEC §3 Out-of-scope와 일관) — 목적은
Harness Gate 마찰을 정직하게 보여주는 것이지 완벽한 점수가 아니다. 위 갭을 감춘 채
릴리스하지 않고, 이 문서에 명시한 채로 인간 승인을 받는다.
