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
