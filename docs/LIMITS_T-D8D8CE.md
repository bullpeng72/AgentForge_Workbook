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
