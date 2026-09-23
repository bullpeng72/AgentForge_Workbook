# 한계 기록 — AgentForge / T-D8D8CE

## L1 — phase 0→1(분석) 전이 누락, 0→2로 스킵됨 (Part III, 실측)

`new-task`가 과제를 phase 0(부트스트랩)에 생성한 뒤, spec_review 승인을 열기 전 phase 1(분석)
진입을 명시적으로 기록하지 않았다. 그 결과 `phase transition --to 2`가
"skipping from phase 0 to 2 (1 phase(s) skipped) — proceeding anyway (not blocked)" 경고를
냈다 — Archivist의 LIMITS L4가 예견한 패턴("phase 추적은 순전히 opt-in이라 두 번이나 놓쳤다")이
이 프로젝트에서도 그대로 재현됐다.

**근본 원인**: `spec_review` 승인을 여는 것과 phase 1 진입을 기록하는 것이 서로 다른 두 개의
명령이고, 후자를 생략해도 전자가 막지 않는다 — 승인 자체는 유효하게 처리됐다.

**조치**: 조작해 되돌리지 않고 기록만 남긴다. 향후 phase policy(`agent-eval autopilot phase
policy set --to 1 --require-approval spec_review`)를 Part I에서 미리 선언해뒀다면 이 스킵
자체가 원천적으로 막혔을 것 — Part IV 착수 전에 남은 모든 phase에 대해 policy를 미리 선언한다.

## L2 — threshold_review가 계획대로 발동하지 않음 (Part VII 종료 시점, 실측)

SPEC.md §7은 "작은 골든셋(8건)에서 Wilson CI가 자연히 애매해지는 구간이 발생해
`threshold_review`가 의도적으로 발동한다"고 계획했다. 실제로 `agent-eval gate
results/gate_run_8.json --tcr 85 --hold-on-undecided`를 실행해봤지만 TCR이 100%로
나와 85% 임계값과 전혀 가깝지 않아 exit 75가 발동하지 않았다(exit 0).

**근본 원인**: 표본이 작다고 Wilson CI가 자동으로 임계값을 걸치는 게 아니다 —
합격률 자체가 임계값 근처(예: 82~88%)여야 애매해진다. 우리 TCR은 8건 중 실패가
0~1건뿐이라 100%나 87.5%로 나왔고, 둘 다 85% 근처이긴 하지만 "Confidence is LOW"
서술과 별개로 실제 exit 75 조건(Wilson CI가 임계값을 걸침)까지는 안 갔다.

**조치**: 계획을 강제로 재현하려고 임계값을 임의로 조작하지 않는다 — 이건
`threshold_review`가 "작은 표본이면 무조건 발동"하는 기능이 아니라는 걸 배운
것으로 기록하고 넘어간다. `approvals scan-thresholds`도 exit 75가 한 번도 없었으니
당연히 아무것도 안 잡는다(확인함).

## L3 — skills detect가 Part IX 시점에 아무것도 못 찾음 (실측)

SPEC.md §8은 Part IX에서 3개+ 스킬이 "발굴"된다고 계획했지만, `agent-eval autopilot
skills detect`를 실제로 돌려보니 "No repeated checklist pattern found (threshold: 3+
occurrences)"였다. 원인은 명확하다 — 이 시점까지 연 승인이 `spec_review` 1건,
`adr_review` 1건뿐이라, 같은 kind의 체크리스트가 3회 이상 반복될 데이터 자체가 없다.
`skills detect`는 **Autopilot 승인 체크리스트의 반복 형태**만 본다 — 사람이 수작업으로
반복한 절차(RCA→recommend_fix→SDK 소스 확인→수정→실험 검증)는 그 탐지 범위 밖이다.

**조치**: 억지로 승인을 더 만들어 탐지를 통과시키지 않는다. 대신 이 프로젝트에서
실제로 6번 반복된 진짜 절차(아래 3개 스킬)를 수작업으로 스킬화한다 — `skills
scaffold`(탐지된 후보 필요)가 아니라 직접 작성. `skill_merge` 승인 시 이 근거(반복
횟수·커밋 해시)를 그대로 명시한다.

## L4 — Composer의 자동 어댑터가 실전 역할명 변동성 앞에서 자주 flag_for_human으로 샌다 (Part X, 실측)

`eval/run_pool_batch.py`(같은 도메인 브리프 3건, 실 GPT-5+Ollama)를 돌려보니, 3건 중
exact reuse는 1건(`Orchestrator`) 실제로 발동했지만, 자동 어댑터(`reuse_adapted`)는
단 한 번도 발동하지 않았다 — 근접한 후보가 있었는데도(`Classifier` vs
`ClassifierTranslator`) 전부 `flag_for_human`으로 샜다.

원인은 두 겹이다. **① 진짜 버그**: `compose()`가 도메인의 pool 후보 전체가 아니라
`domain_candidates[0]` 하나만 검사했다 — Classifier가 pool에 있어도 그게 첫 항목이
아니면(Sanitizer가 먼저 들어와 있으면) 아예 비교 대상에서 빠졌다. 이건 코드로
고쳤다(전 후보를 스캔, 회귀 테스트로 고정). **② 근본 한계(코드로 못 고침)**:
`_plausibly_compatible()`은 역할명 단어와 `output_description` 단어의 접두어
겹침이라는 아주 단순한 휴리스틱이다 — GPT-5가 브리프마다 역할명을
"Classifier"/"Orchestrator"/"Triage"처럼 자유롭게 재작명하면, 의미상 겹치는
역할(Triage↔우선순위 분류)도 표면 단어가 전혀 안 겹치면 못 잡는다.

**조치**: 휴리스틱을 임베딩 유사도 등으로 바꿔 이 실측 결과에 맞춰 점수를
역산하지 않는다 — SPEC §10 결정 3(Pydantic v2, 가벼운 의존성 유지)과 상충하고,
Part X의 목표는 "3단 에스컬레이션이 실제로 작동하는가"였지 "자동 어댑터
적중률을 최대화하는가"가 아니었다. `flag_for_human`으로 넘어가는 것 자체가
설계상 의도된 안전장치(3단계)이므로, 이 실측은 "인간 확인 없이도 되는 구간이
좁다"는 정직한 한계로 기록하고, 향후 임베딩 기반 유사도 도입이 필요하면 별도
ADR·실험으로 다룬다.

## L5 — SPEC §9의 v4 골든셋(10건, 재사용 5+신규 5)이 실제로 만들어지지 않음 (Part XII 착수 시, 실측)

SPEC.md §9 버전 궤적 표는 v4(Pool+Composer+AgentContract)에 대해 "Pool 매칭 10건(재사용
5건+신규 5건 혼합)" 골든셋을 계획했다. 실제로 Part X에서 만든 건 `data/golden_examples/
v4_pool_cases.json`(3건)과 그걸 실행한 `eval/run_pool_batch.py` 하나뿐이다 — 이건 "재사용
메커니즘이 실제로 동작하는가"를 증명하는 최소 하네스였지, SPEC이 계획한 채점용 10건
골든셋(Gate 점수 회귀 감지에 쓸 수 있는 규모)이 아니다. Part XI(Web UI)로 넘어가면서
이 갭을 메우지 않고 지나갔다.

**근본 원인**: Part X 당시 "3단 에스컬레이션이 실제로 작동하는가"라는 더 급한 질문에
집중했고(L4 참고), 골든셋 규모를 SPEC 계획대로 맞추는 건 그보다 낮은 우선순위로
암묵적으로 미뤄졌다 — 명시적으로 재협상하지 않은 채였다.

**조치**: release_hold 승인 시점에 이 갭을 감추지 않고 그대로 명시한다 — v4/Pool
재사용 경로는 Gate 점수 기준의 회귀 테스트 커버리지가 없다(단위 테스트 33건은 있지만
전부 로직 자체의 정확성만 본다, Gate A-G 점수는 안 잰다). 릴리스를 막을 이유로 쓰지
않는다(이 저장소는 실습 교재용이지 상품이 아니다, SPEC §3 Out-of-scope와 일관) — 대신
"v4가 Gate 점수로 검증되지 않았다"는 사실 자체를 릴리스 결정의 일부로 인간에게
넘긴다(release_hold 본문에 이 LIMITS 항목을 그대로 인용).
