# 회고 — AgentForge (T-D8D8CE, Part XIII)

phase 8(운영) 도달 시점(`phase8-operations`)의 실측 기반 회고. 전부 `results/`·`.aoo/`의
실제 파일에서 뽑았다 — 추정이나 목표치가 아니다.

## 1. SPEC §11 완료 정의(DoD) — 실측 대조

| 항목 | 상태 | 근거 |
|---|---|---|
| F1–F12 전부 골든셋 케이스로 검증됨 | **부분** | F1-F4는 8건 골든셋(`gate_run_8.json`)으로 검증. F5-F8은 3건 실측 하네스(`v4_pool_cases.json`, SPEC이 계획한 10건 아님 — LIMITS L5)로 메커니즘만 검증, Gate 점수 회귀 커버리지 없음. F9-F12는 SPEC §9 자체가 "골든셋 대상 아님, 수동 QA"로 계획했고 실제로 수동 QA(오프라인 TestClient 18건 + 실 서버 curl 검증, Part XI)로 검증 — 골든셋 방식이 아니라는 점에서 항목 문구 그대로는 미충족이지만 SPEC이 의도한 검증은 완료 |
| Gate A–G 7개 전부 fail 경유 → `improve verify` confirmed 완주 | **부분(4/7 대상, 3/4 완주)** | 실제 fail한 건 A·C·D·F뿐(LIMITS L6). A·C·D는 confirmed까지 완주. F는 fail(run4)했지만 별도 하네스(`gate_f_run.json`) 설계 때문에 이 개선루프 대상에서 구조적으로 빠짐. B·E·G는 한 번도 fail/warn을 겪지 않아 애초에 이 DoD의 모집단이 아님 |
| 6개 승인 kind 전부 실제 발동 | **부분(5/6)** | spec_review·adr_review·skill_merge·release_hold·deploy 전부 실제 발동·완료. threshold_review는 계획대로 발동하지 않음(LIMITS L2 — TCR이 85% 임계값과 멀어 Wilson CI가 걸치지 않음) |
| 2인 팀 + 진짜 GitHub 원격에서 클레임 충돌 최소 1회 실전 발생·해소 | **완료** | `.aoo/claims.jsonl`: 채린이 `src/agentforge/`(광범위)를 클레임할 때 지호의 기존 `src/agentforge/verifier/`와 실제로 겹침 → 채린이 12초 만에 반납하고 `.github/workflows/`로 좁혀 재클레임(실전 해소) |
| Skills 3개+ 신규 발굴 및 `skill_merge` 승인 | **완료** | `evidence-based-gate-fix`·`background-real-verification`·`honest-refuted-experiment-logging` 3종, `skill_merge` 승인(phase 4→6) |
| Pool 재사용률·Compose 성공률 정량 보고 | **완료(아래 §2)** | — |

## 2. Pool 재사용률 · Compose 성공률 (실측)

`eval/run_pool_batch.py` 실행 결과(`results/gate_run_pool.json`, 실 GPT-5+Ollama, 같은 도메인
브리프 3건 → 역할 판단 6건). **표본이 매우 작다(실 API 비용 때문에 3건으로 제한) — 통계적
의미가 아니라 메커니즘 증거로 읽는다.**

| 호출 순서 | 역할 | 판단 | Pool에 같은 도메인 후보가 있었나 |
|---|---|---|---|
| 1 (`v4-01-support-base`) | Sanitizer | generate_new | 아니오(Pool 비어있음) |
| 1 | Classifier | generate_new | 아니오 |
| 2 (`v4-02-support-extended`) | Orchestrator | flag_for_human | 예 |
| 2 | ClassifierTranslator | flag_for_human | 예 |
| 3 (`v4-03-support-triage`) | Triage | flag_for_human | 예 |
| 3 | Orchestrator | **reuse_exact** | 예 |

- **Pool 재사용률**(전체 6건 중 완전/자동어댑터 재사용) = 1/6 = **16.7%**
- **Pool과 조우한 시도 중 재사용률**(도메인 후보가 실제로 있었던 4건 중) = 1/4 = **25%**
- **Compose 성공률**을 "재사용(exact+adapted)"로 정의하면 위와 같고, "3단 에스컬레이션이
  올바른 판단을 내렸는가"(사람에게 넘겨야 할 걸 넘기고, 재사용할 수 있는 걸 재사용했는가)로
  정의하면 **6/6 = 100%**다 — `flag_for_human` 3건은 전부 실제로 무관한 역할이었고(오판이
  아니었다는 건 LIMITS L4에서 근본원인을 직접 확인함: 1단계 버그 수정 후에도 표면 단어가
  안 겹쳐 자동 어댑터가 못 잡은 것), 사람에게 넘긴 게 맞는 판단이었다.
- **reuse_adapted(자동 어댑터)는 이 3건짜리 실측에서 단 한 번도 발동하지 않았다** — LIMITS
  L4의 핵심 발견. 단위 테스트(`test_pool_composer.py`)에서는 합성 데이터로 발동을 확인했지만,
  실제 GPT-5 역할명 변동성 앞에서는 아직 실증되지 않은 경로다.

## 3. 세 책 9+2지표 비교 (Archivist·SupportTriage·AgentForge)

**이 항목은 이 저장소만으로 완결할 수 없어 미룬다.** Archivist(`AOO_Autopilot_Workbook`)와
SupportTriage(AC책)의 실제 최종 지표는 그 두 저장소 자신의 `results/`에 있고, 이 세션은 그
두 저장소를 열어 실측 대조하지 않았다 — 기억에 의존한 근사치를 여기 적으면 "실측"이 아니라
"추정"이 되어 이 프로젝트 전체의 원칙(허구 수치 금지)에 어긋난다. 실제 집필 시점에 세 저장소를
모두 열어 각자의 `results/final/*.json`을 대조해 채운다.

## 4. 한눈에 — 무엇이 정말 어려웠나

- **Gate D(성능계약)는 끝내 안 풀렸다.** 두 번의 진짜 개선 시도(exp-b6bb316243 확인·delta,
  exp-ea6762633c 재설계) 모두 `improve verify`로 confirmed 판정을 받았지만, 점수 자체는
  0.6347로 0.7 문턱을 못 넘겼다 — "측정을 정직하게 고친 것"과 "성능이 실제로 좋아진 것"은
  다르다는 걸 이 프로젝트가 직접 겪었다.
- **Composer의 진짜 어려움은 코드가 아니라 실세계 데이터였다.** 로직 버그(L4의 1단계, 첫
  후보만 보던 것)는 실측 한 번으로 잡혔지만, 그 다음 남은 문제(자동 어댑터가 GPT-5의 역할명
  변동성을 못 따라감)는 코드로 못 고친다 — 임베딩 유사도 같은 다른 접근이 필요하다는 걸
  실측으로 확인했을 뿐, 고치진 않았다(의도적으로, ADR과 상충하지 않는 선에서).
- **DoD를 글자 그대로 채우려 하지 않은 것 자체가 이 프로젝트의 태도였다.** Gate B·E·G를
  억지로 fail시켜 "7개 전부 완주"를 만드는 대신, "애초에 실패한 적이 없다"는 사실을
  그대로 인정했다(LIMITS L6).
