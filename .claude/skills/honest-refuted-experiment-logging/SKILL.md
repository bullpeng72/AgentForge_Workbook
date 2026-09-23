---
name: honest-refuted-experiment-logging
description: agent-eval experiment/improve verify 결과가 refuted(가설이 틀렸다)로 나왔을 때, 이걸 지우거나 조용히 넘어가지 않고 커밋·문서에 그대로 남기는 절차. "이 수정이 예상대로 안 통했다", "잘못된 필드를 예측했다" 같은 상황에서 사용한다.
aoo_dependency: full
---

# honest-refuted-experiment-logging — 틀린 가설도 기록한다

AgentForge에서 실제로 4번 refuted가 나왔다: `exp-d2ff2b6850`(D.p95_latency_s, 잘못된
필드 선택), `exp-5774953dab`(C.reproducibility, seed만으론 결정성 보장 안 됨),
`exp-14f651addf`(D.p95_latency_s, 뒤늦게 검증해 비교 대상이 안 맞음). 매번 지우고
다시 시도할 수도 있었지만, 전부 `.aoo/experiments.jsonl`에 남겼고 커밋 메시지에도
"왜 틀렸는지"를 적었다.

## 왜 필요한가

refuted 실험을 지우면 두 가지를 잃는다 — ① 같은 실수를 나중에 반복할 위험(예:
"D.p95_latency_s를 recalibration으로 못 바꾼다"는 교훈이 사라짐), ② `recommend_fix`의
track record 인용 기능(`.aoo` 로그 기반)이 실패 사례를 못 보고 성공 사례만 보여줘
과신을 유도함. 원칙2("통과보다 증명이다")는 성공만 증명하라는 뜻이 아니다 — 틀렸다는
것도 증명이다.

## 절차

1. `agent-eval improve verify`가 refuted를 반환하면, 그 실험을 삭제하거나 로그에서
   빼지 않는다 — `--persist`로 그대로 남긴다.
2. 왜 틀렸는지 원인을 한 문장으로라도 파악한다(추측 금지 — 가능하면 SDK 소스나
   실측 데이터로 확인). 모르면 "원인 불명"이라고 솔직히 적는다.
3. 다음 커밋 메시지에 "이전 실험 X는 refuted였다, 이유는 Y였다"를 명시한다 —
   최종 성공만 적고 실패 시도를 감추지 않는다.
4. 같은 필드를 다시 예측할 일이 생기면, refuted 이력을 먼저 확인한다
   (`.aoo/experiments.jsonl` 또는 `recommend_fix`가 인용하는 prior).
5. refuted가 여러 번 쌓이면(같은 gate, 같은 접근) — 그 접근 자체를 포기할
   근거로 삼는다. 계속 다른 숫자만 바꿔가며 재시도하지 않는다.

## 완료 조건

- [ ] refuted 실험을 `.aoo/experiments.jsonl`에서 지우지 않았다
- [ ] 왜 틀렸는지 원인(또는 "불명")을 커밋 메시지나 문서에 적었다
- [ ] 이후 같은 필드를 다시 만졌다면 이 이력을 먼저 확인했다
