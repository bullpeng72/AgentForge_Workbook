---
name: evidence-based-gate-fix
description: Gate 점수가 fail/warn일 때, SDK 소스 코드를 직접 읽어 채점 공식을 확인한 뒤 조치하는 절차. 추측으로 임계값을 조정하지 않는다. "Gate D가 왜 이 점수인지 정확히 모르겠다", "recommend_fix가 준 조언이 너무 일반적이다" 같은 상황에서 사용한다.
aoo_dependency: full
---

# evidence-based-gate-fix — SDK 소스 기반 Gate 수정 절차

AgentForge Part VII에서 6번 반복하며 확립된 절차다(Gate C SLA 재보정, Gate D
재현성-실행시간 오염, Gate A 응답품질, Gate C/F seed, Gate D monitor 분리+비용예측성,
Gate D SLA 재설계 — commit `78d1c913`·`706bcbf3`·`a26daf36`·`0faa251c`·`324d483`·
`c341273c`). `agent-eval autopilot skills detect`는 Autopilot 승인 체크리스트의
반복만 보기 때문에 이런 수작업 절차 반복은 못 잡는다(LIMITS L3) — 그래서 손으로
스킬화한다.

## 왜 필요한가

`recommend_fix`(MCP)는 Gate 단위 일반 조언만 준다("ScopeConfig/ConflictResolutionConfig를
추가하라"). 구체적 metric(예: `sla_breach_rate`, `avg_cost_predictability`)의 정확한
계산식은 알려주지 않는다. 이 계산식을 모른 채 임계값을 조정하면 "왜 됐는지" 모르는
채로 우연히 점수만 오르는 결과가 나온다 — 다음에 비슷한 문제가 생기면 다시 처음부터
헤맨다.

## 절차

1. `agent-eval diagnose <result> --baseline <baseline> --show-diff`로 어느 Gate·어느
   detail metric이 떨어졌는지 RCA부터 확인한다.
2. `recommend_fix` MCP를 gate+metric으로 호출해 일반 조언과 과거 track record를
   확인한다.
3. **일반 조언이 구체적이지 않으면, SDK 소스에서 그 metric의 정확한 계산식을
   찾는다** — `agent_evaluator/gates/gate_<x>_*/aggregate.py` 또는
   `core/trackers/*.py`에서 해당 필드명으로 grep. 공식을 손으로 재계산해 실제
   결과값과 일치하는지 검증한다(가정이 아니라 확인).
4. 공식을 이해한 뒤에만 조치를 설계한다 — 임계값 조정이라면 "왜 기존 값이
   이 파이프라인 성격과 안 맞는지" 근거를 댈 수 있어야 한다(예: 동기 채팅 기준
   임계값을 비동기 생성 작업에 그대로 쓴 것).
5. `agent-eval experiment register --gate X --field Y --predict-delta Z`로 조치
   **전에** 예측을 문서화한다(원칙1).
6. 조치를 적용하고 실제로 재측정한다(mock 아님 — 진짜 API/서버 호출).
7. `agent-eval improve verify <new> --baseline <old> --persist`로 confirmed/refuted를
   공식 기록한다. **refuted가 나와도 지우지 않는다** — `honest-refuted-experiment-logging`
   스킬 참고.

## 완료 조건

- [ ] RCA(`diagnose`)로 원인 metric을 먼저 특정했다(추측으로 시작 안 함)
- [ ] SDK 소스에서 그 metric의 계산식을 확인했다(파일 경로·줄 번호를 커밋 메시지에 남김)
- [ ] 손으로 재계산한 값이 실제 결과와 일치함을 확인했다
- [ ] 조치 전에 `experiment register`로 예측을 남겼다
- [ ] 실제 재실행(mock 아님)으로 재측정했다
- [ ] `improve verify --persist`로 confirmed/refuted를 공식 기록했다
