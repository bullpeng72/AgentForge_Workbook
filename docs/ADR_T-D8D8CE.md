# ADR — AgentForge 아키텍처 결정 (T-D8D8CE)

> 《하네스 메서드》 §17 ADR 형식. `adr_review` 승인 대상. SPEC.md §10의 3개 가결정을
> 여기서 공식 재확인하고, 5-컴포넌트 역할분리 + Tier1/2 배정을 신규로 결정한다.

## 배경

SPEC.md(승인됨, `spec-approved`)가 F1–F12를 정의했다. 이 요구사항을 몇 개 컴포넌트로 나누고,
각각을 Tier 1(AC/클라우드, 넓은 판단)·Tier 2(AOO/로컬, 좁은 실행) 중 어디에 배정할지가
아직 근거와 함께 문서화되지 않았다(원칙5: "이 배정을 설계 단계 산출물의 모델 배정 항목으로
남긴다"). 이 ADR이 그 문서다.

## 결정 1 — 5-컴포넌트 역할 분리

| 컴포넌트 | 담당 요구사항 | 입력 | 출력 |
|---|---|---|---|
| Spec Interpreter | F1 | 자연어 브리프 | Golden Data(목표·제약·성공기준) |
| Team Designer | F2 | Golden Data | 역할분담 설계(몇 개 에이전트, 각 책임) |
| Code Generator | F3, F8(신규분만) | 역할분담 설계 | `agents.yaml`/`tasks.yaml`/`crew.py` |
| Verifier | F4 | 생성 코드 | smoke-test 결과 + 골든셋 + `@agent_eval` 배선 |
| Composer | F5–F8 | 새 브리프 + Pool | 재사용 매칭 + 부족분 위임 + 최종 팀 구성 |

**대안 검토**: Spec Interpreter와 Team Designer를 하나로 합치는 안을 검토했으나 기각 —
"브리프 해석"과 "팀 구조 설계"는 서로 다른 실패 모드(전자는 파싱 실패, 후자는 설계-구현
불일치)를 가져 Gate A(F1 담당)와 Gate F(F2/F3 경계) 진단이 뒤섞인다. 분리 유지.

## 결정 2 — Tier 1/2 배정 (원칙5: 추론깊이·도구폭·지연예산·blast radius)

| 컴포넌트 | Tier | 추론깊이 | 도구폭 | 지연예산 | blast radius | 근거 |
|---|---|---|---|---|---|---|
| Spec Interpreter | **1**(AC) | 높음 | 좁음 | 여유(사람 승인 전 1회) | 큼(여기서 틀리면 전부 틀림) | 모호한 브리프의 여러 해석 중 저울질 |
| Team Designer | **1**(AC) | 높음 | 좁음 | 여유 | 큼(설계 오류가 Code Generator까지 전파) | 분할 방식 여러 안을 비교 판단 |
| Code Generator | **2**(AOO) | 낮음 | 넓음(파일쓰기) | 타이트(v2 반복 재생성) | 작음(Verifier가 바로 검증) | 주어진 설계를 좁혀진 지시로 따름 |
| Verifier | **2**(AOO) | 낮음 | 넓음(실행+생성) | 타이트(매 생성마다) | 작음 | 정해진 체크리스트 실행 |
| Composer | **1**(AC) | 높음 | 좁음(검색+매칭) | 여유(팀 구성은 1회성) | 큼(오매칭이 전체 팀 품질에 영향) | 여러 Pool 후보 중 저울질 판단 |

**대안 검토**: Composer를 Tier 2로 두는 안을 검토했으나 기각 — Pool 매칭은 "좁혀진 지시를
따르는" 실행이 아니라 "여러 후보 중 어느 것이 맞는지 판단"하는 넓은 추론이라 원칙5의 Tier 1
기준(추론깊이·blast radius)에 더 부합한다.

정확한 모델 이름·버전 핀은 이 ADR의 범위가 아니다 — Part V(v0 착수) 시점에 `models.lock`으로
별도 확정한다(원칙5 §9: Tier 배정과 모델 핀은 별개 결정).

**개정(Part VI, v2 완료 후)**: Tier 1 모델을 claude-sonnet-5 → gpt-5(OpenAI)로 전환했다.
ANTHROPIC_API_KEY를 끝내 확보하지 못해 Tier 1 구간(Spec Interpreter·Team Designer)이 v2까지
계속 mock 상태로 남아 있었다 — Tier 배정(축·근거)은 프로바이더와 무관하므로 결정 자체는
그대로 유지하고, `models.lock`의 모델 핀만 바꿨다. `AnthropicClient`는 `llm/client.py`에
대체 프로바이더로 남겨뒀다(LLMClient 프로토콜만 맞으면 언제든 되돌릴 수 있음).

## 결정 3 — AgentContract 스키마 = Pydantic v2 (SPEC §10 재확인)

CrewAI 생태계 자체가 Pydantic v2 기반이라 별도 스키마 언어를 새로 배울 필요가 없고,
`agent-evaluator`의 기존 모델 타입 체계와도 일치한다. **변경 없이 확정.**

## 결정 4 — Pool 저장 = `results/*.json` + SQLite 검색 인덱스 하이브리드 (SPEC §10 재확인)

Verifier(F4)가 이미 생성하는 평가 결과 파일이 원천 데이터, 그 위에 `agent_evaluator.storage.
sqlite_backend`의 기존 패턴을 재사용한 검색 인덱스만 추가한다. 별도 Pool 전용 DB 스키마를
새로 설계하지 않는다(원칙4). **변경 없이 확정.**

## 결정 5 — Web UI 스택 = FastAPI + Jinja2 (재확인)

Autopilot 대시보드(`autopilot_app.py`, port 8766)와 동일 패턴 — React 등 신규 프런트엔드
스택을 도입하지 않는다. 독자가 이미 Part I~III에서 이 패턴을 접했으므로 학습 부담이 없다
(원칙4). 인증/권한관리는 SPEC §3 Out-of-scope와 일치, 범위 밖 유지.

**Part XI 착수 시 정정(실측)**: "동일 패턴 재사용"을 실제로 구현하려고
`agent_evaluator/serve/autopilot_app.py` 소스를 직접 확인해보니, 그 파일은 Jinja2 엔진을
전혀 쓰지 않는다(`jinja2` import 없음, `.j2` 템플릿 없음, `Jinja2Templates` 없음) —
`html.escape` 기반 `_esc()` 헬퍼 + `_layout()` f-string으로 순수 서버 렌더 HTML을 직접
조립하는 패턴이다(`serve/templates/dashboard2.html.j2`를 쓰는 8765번 포트의 결과
대시보드와는 다른 계열). SPEC.md §3·§10의 "FastAPI+Jinja2" 표기는 부정확했다 —
"동일 패턴 재사용"이라는 원래 의도(원칙4, 학습 부담 최소화)를 살리려면 실제로 재사용되는
그 패턴(raw f-string + `_esc()`)을 따라야 한다. AgentForge Web UI는 이 실측된 패턴대로
구현하고, `pyproject.toml`의 미사용 `jinja2` 의존성은 제거한다. SPEC.md 표기는 그대로
"Jinja2"로 남겨두지 않고 이 ADR과 함께 정정한다.

## 결정 6 — Pool 항목의 Gate 점수 조회 경로 (Part XI 착수 시 신규)

F9(Pool 브라우저에서 Gate 점수로 검색/필터)를 구현하려면 각 pooled 에이전트가 실제로
측정된 Gate A–G 점수를 가리킬 수 있어야 한다. 그런데 `PoolIndex`의 `source_task_id`는
SQLite PRIMARY KEY라 **pool 항목 하나마다 고유**해야 하고(`_populate_pool`이 한 번의
생성 호출에서 여러 역할을 만들 때마다 역할별로 다른 값을 쓰는 이유), 반면 `results/*.json`
안의 실제 평가 task_id는 **한 번의 파이프라인 실행(호출) 단위**로 하나뿐이다 — 여러 역할이
같은 task_id를 공유한다. 이 둘을 같은 필드로 억지로 합치면 SQLite `INSERT OR REPLACE`가
같은 PK를 가진 앞선 역할의 pool 항목을 조용히 덮어써 데이터를 잃는다(실측 확인, 코드
변경 전에 스키마를 다시 읽어 잡음).

**결정**: `AgentContract`에 `origin_task_id: str | None`을 별도 필드로 추가한다.
`source_task_id`(pool 항목 고유 PK, 기존 그대로)와 `origin_task_id`(이 항목을 만든
평가 실행의 실제 task_id, 여러 역할이 공유 가능)를 분리한다. Web UI의 Pool 브라우저는
`origin_task_id`로 `results/*.json`을 역참조해 Gate 점수를 조회한다(결정 4의 "하이브리드"
원안을 실제로 작동하게 만드는 보완) — 새 DB 스키마나 점수 중복 저장은 하지 않는다(원칙4
그대로 유지).

## 결과 / 트레이드오프

- Tier 1 컴포넌트 3개(Spec Interpreter·Team Designer·Composer) 모두 클라우드 호출이라,
  Gate D(비용·지연)에서 Tier 1 비중이 단일 에이전트 파이프라인보다 높게 나올 것으로
  예상된다 — Part VII에서 실측하고, 필요하면 `tier_downshift` 신호를 검토한다.
- Composer를 Tier 1으로 둔 결정은 Pool이 커질수록(재사용 후보가 많아질수록) 지연이 늘어날
  잠재 리스크가 있다 — Part X(Pool과 재사용) 착수 시 재검토 대상으로 남긴다.
