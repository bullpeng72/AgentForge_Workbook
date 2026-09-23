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

## 결과 / 트레이드오프

- Tier 1 컴포넌트 3개(Spec Interpreter·Team Designer·Composer) 모두 클라우드 호출이라,
  Gate D(비용·지연)에서 Tier 1 비중이 SupportTriage류 단일에이전트보다 높게 나올 것으로
  예상된다 — Part VII에서 실측하고, 필요하면 `tier_downshift` 신호를 검토한다.
- Composer를 Tier 1으로 둔 결정은 Pool이 커질수록(재사용 후보가 많아질수록) 지연이 늘어날
  잠재 리스크가 있다 — Part X(Pool과 재사용) 착수 시 재검토 대상으로 남긴다.
