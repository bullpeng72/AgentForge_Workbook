# SPEC — AgentForge

> 신규 워크북(《AgentForge 실습서》)의 예제 과제 명세. 《하네스 메서드》 §15.1 Spec 형식을 따른다.
> 상태: DRAFT — Part III(분석)에서 `spec_review` 승인 전까지는 확정이 아니다.

## 1. 목표

자연어 브리프 하나를 받아 실행 가능한 CrewAI 멀티에이전트 팀(코드+평가 스캐폴드)을 생성하고, 이미 만든 에이전트를 Pool에 쌓아 재사용하며, 이 전 과정을 Web UI로 조작할 수 있는 도구 **AgentForge**를 만든다. 이 개발 자체를 하네스 방법론 + AOO/AC 혼합 + Autopilot + Skills로 진행해, 두 기존 워크북(Archivist·SupportTriage)이 규모 부족으로 못 채운 지점(Gate F 실측·6종 승인 전부·팀 협업 실전 검증)을 전부 채운다.

## 2. 배경

- 기존 두 워크북은 각각 Gate F를 별도 하네스로 재거나(Archivist) 계약만 설계하고 실측하지 않았다(SupportTriage, 00_서문.md 자인).
- Autopilot·Skills는 두 책이 쓰인 시점 이후 추가된 기능이라 애초에 겨냥해 설계되지 않았다.
- 외부 리서치(2026-09 조사)로 CAAS·`multi-agent-generator`(PyPI) 같은 "자연어→멀티에이전트 생성기" 도구가 이미 존재하며, 그중 `multi-agent-generator`는 평가 프레임워크를 이미 내장하고 있음을 확인했다 — AgentForge는 이 방향이 실제로 가치 있다는 외부 검증을 갖고 시작한다(단, 시장 경쟁력이 아니라 **방법론 교재**로서의 가치가 목적).

## 3. 범위

**In-scope**
- 출력 프레임워크: **CrewAI 하나만**(스코프 폭발 방지 — CAAS 사례에서 배운 교훈)
- 버전 v0–v5(§9)
- Agent Pool 재사용 + Composer + AgentContract 호환성 체크
- FastAPI Web UI(Autopilot 대시보드와 동일 패턴 재사용 — 실측 정정: 그 패턴은 Jinja2 엔진이
  아니라 순수 f-string HTML + `html.escape`다, ADR_T-D8D8CE.md 결정 5 참고)

**Out-of-scope (명시적 비목표)**
- LangGraph·Agno·ReAct 등 타 프레임워크 출력 — `multi-agent-generator`가 이미 하는 영역, 재발명 안 함(원칙4)
- 크로스팀·크로스프로젝트 Pool 공유(포트폴리오 단위) — L5(조직 확장) 밖, 단일 팀 범위로 한정
- 프로덕션 멀티테넌시·과금 — 교재용 예제이지 상품이 아님
- Web UI 인증/권한관리 — §10 결정사항 참고, 단일 팀 로컬 실행 전제

## 4. 기능 요구사항

| ID | 요구사항 | 대응 에이전트/컴포넌트 |
|---|---|---|
| F1 | 자연어 브리프를 구조화된 Golden Data(목표·제약·성공기준)로 변환한다 | Spec Interpreter |
| F2 | Golden Data를 몇 개 에이전트로 나눌지, 역할을 어떻게 분담할지 설계한다 | Team Designer |
| F3 | 설계를 실제 CrewAI 코드(`agents.yaml`/`tasks.yaml`/`crew.py`)로 변환한다 | Code Generator |
| F4 | 생성 코드를 smoke-test 실행하고, 결과물용 골든셋+`@agent_eval` 배선을 자동 생성한다 | Verifier |
| F5 | 새 브리프가 들어오면 Pool에서 재사용 가능한 에이전트를 먼저 찾는다 | Composer |
| F6 | Pool에서 찾은 에이전트를 새 팀에 연결할 때 AgentContract(I/O 스키마) 호환성을 검사한다 | Composer + AgentContract |
| F7 | 스키마 불일치 시 3단 에스컬레이션(완전일치→자동어댑터→사람 flag)으로 처리한다 | Composer |
| F8 | Pool 부족분(찾지 못한 역할)만 F2·F3으로 신규 생성한다(전체 재생성 금지) | Composer→Team Designer/Code Generator |
| F9 | Web UI에서 Pool을 역할·Gate 점수·I/O 계약으로 검색/필터할 수 있다 | Web UI — Pool 브라우저 |
| F10 | Web UI에서 에이전트를 선택해 연결선(wiring)을 구성하고 즉시 호환성 피드백을 받는다 | Web UI — Compose 화면 |
| F11 | Web UI에서 구성된 팀의 Gate A–G 스코어카드를 볼 수 있다 | Web UI — 평가 화면(`evaluation.html` 임베드) |
| F12 | Web UI에서 해당 팀이 어느 Autopilot 승인 단계에 있는지 볼 수 있다 | Web UI — 승인 현황(Autopilot 상태 조회) |

## 5. 비기능 요구사항

| ID | 요구사항 | 검증 방법 |
|---|---|---|
| NF1 | 같은 브리프를 두 번 넣으면 동일한 구조의 팀이 나온다(재현성) | Gate C, seed 고정 |
| NF2 | Pool 재사용 에이전트가 원버전에서 회귀하면 감지된다 | `agent-eval gate --baseline-version` per-agent |
| NF3 | Code Generator가 스코프 밖(비CrewAI) 코드를 생성하지 않는다 | Gate B, `ScopeConfig` |
| NF4 | 생성 코드에 위험 명령·시크릿 하드코딩이 없다 | Gate E |
| NF5 | 4~5개 에이전트 파이프라인의 지연·비용이 Part VII 진단→개선을 거쳐 실측 가능한 수준으로 통제된다 | Gate D, Tier2 캐싱 |
| NF6 | 각 단계의 선택 이유가 기록된다(explainability) | Gate G, `require_reasoning` |

## 6. 실패 모드 카탈로그

| 실패 모드 | 증상 | 대응 |
|---|---|---|
| 모호한 브리프 파싱 실패 | Spec Interpreter가 목표를 잘못 추출 | Gate A 하락 → few-shot 보강(Part VII) |
| 설계-구현 불일치 | Team Designer 설계를 Code Generator가 다르게 구현 | Gate F 하락 → 인터페이스 명시화 |
| 비결정적 생성 | 같은 브리프, 다른 결과 | Gate C 하락 → seed 고정 |
| Pool 오매칭 | Composer가 브리프와 안 맞는 에이전트를 재사용 | Gate A(신규 축) 하락 → 매칭 기준 재조정 |
| 스키마 불일치 방치 | 자동 연결됐지만 실제로는 데이터가 안 맞음 | F7 3단 에스컬레이션 3단계(사람 flag)로 처리 |
| Pool 버전 드리프트 | 재사용 에이전트가 업데이트됐는데 기존 조합이 모르고 계속 씀 | NF2, `agent-contract-versioning` skill |
| **LLM 출력 이스케이프 오류**(실측, v2) | Ollama가 낸 JSON에 잘못된 `\` 이스케이프가 섞여 `json.loads` 자체가 실패 | `eval/smoke_full.py` mock 없는 첫 실행(8건 중 1건)에서 실측. Gate C 하락 대상 — 재시도 또는 응답 정제 로직 필요(Part VII) |
| **agents.yaml 최상위 키 누락**(실측, v2) | Code Generator가 `agents:` 키 없이 목록만 내보내 Verifier가 "목록이 없거나 비어 있음"으로 정확히 차단 | 같은 실행에서 실측(8건 중 1건). Verifier가 설계대로 작동한 사례 — Gate C/D 하락 대상, 프롬프트에 스키마 예시 추가 검토(Part VII) |

## 7. Autopilot 활용 계획

| Phase | 무엇을 | 승인 kind |
|---|---|---|
| 0 부트스트랩 | 2인 팀 + GitHub 원격 + `.aoo/` 설치(Part I) | — |
| 1 분석 | 이 SPEC.md 확정(Part III) | `spec_review` |
| 2 설계 | 4(+1)-에이전트 역할분리 + Tier1/2 배정 ADR(Part IV) | `adr_review` |
| 3 개발(TDD-AI) | v0→v3 구현(Part V–VII) | — |
| 4 검증 | Gate A–G 전부 fail→진단→해결 호 완성(Part VII) | `threshold_review`(작은 골든셋에서 의도적으로 발동) |
| 5 팀·PR CI | 클레임 충돌 실전 발생(Part VIII) | — |
| 6 Skills화 | 3개+ 스킬 발굴(Part IX) | `skill_merge` |
| 7 Pool·Web UI 확장 | v4·v5 구현(Part X–XI) | — |
| 7→8 릴리스 후보 | v3→v5 배포 전 | `release_hold`(2인) |
| 8 운영 | 최종 릴리스(Part XII) | `deploy`(2인) |

6개 승인 kind 전부 설계상 발동 지점이 명시돼 있다 — Archivist처럼 우연히 발동하는 것이 없다.

## 8. Skills 활용 계획

**기존 Agent-Evaluator Skills 중 이 프로젝트에서 실사용**: `spec-driven-artifacts`(본 SPEC 작성) · `harness-gate-ci` · `gate-improvement-loop`(Part VII) · `recommend-fix-workflow` · `abtest-decision-workflow`(v0–v5 버전 비교) · `tdd-ai-workflow-checklist` · `config-silent-noop-check` · `eval-run-directory-hygiene` · `claims-audit-ci`(Part VIII) · `checklist-confidence-audit` · `threshold-realism-review` · `sync-drift-check` · `harness-autopilot` · `unattended-session-recovery`.

**이 프로젝트에서 신규 발굴 예정**(Part IX·X):
- `pool-compatibility-check` — AgentContract 스키마 대조 절차
- `agent-contract-versioning` — pooled 에이전트 버전 변경 시 하위 조합에 전파하는 절차
- `webui-dashboard-scaffold` — FastAPI + f-string HTML(`html.escape`, Jinja2 미사용)로 SDK 대시보드 패턴을 재사용해 새 화면을 붙이는 절차(Autopilot 대시보드 코드에서 패턴 추출). Part XI에서 실제로 이 절차를 한 번 밟았지만 아직 3회+ 반복은 아니다 — `skills detect` 기준(3회+)을 채우면 그때 실제 스킬화한다(L3와 같은 원칙, 억지로 미리 만들지 않는다).

## 9. 버전 궤적 / 골든셋

| 버전 | 내용 | 골든셋 최소 사례 |
|---|---|---|
| v0 | 규칙기반 스텁 | 4건(파이프라인 형태 증명) |
| v1 | Spec Interpreter·Team Designer LLM화 | 6건 |
| v2 | Code Generator·Verifier 실제화 | 8건(threshold_review 발동 구간) |
| v3 | 결과물용 골든셋+`@agent_eval` 자동배선 | 8건 유지, 메타 검증(생성된 골든셋 자체의 타당성) 추가 |
| v4 | Pool+Composer+AgentContract | Pool 매칭 10건(재사용 5건+신규 5건 혼합) |
| v5 | Web UI | 골든셋 변경 없음(UI는 골든셋 대상이 아님, 수동 QA로 검증) |

## 10. 설계 결정 (구 NEEDS CLARIFICATION, Part IV ADR에서 재확인 예정)

- **AgentContract 스키마 언어**: **Pydantic v2**로 확정. CrewAI 생태계 자체가 Pydantic v2 기반이라 별도 스키마 언어를 새로 배울 필요가 없고, `agent-evaluator`의 기존 모델들과도 타입 체계가 일치한다.
- **Pool 저장 위치**: **하이브리드**로 확정 — `results/*.json`(Verifier가 이미 생성하는 평가 결과)이 원천 데이터(source of truth)이고, 그 위에 검색용 SQLite 인덱스 하나만 얹는다(`agent_evaluator.storage.sqlite_backend`의 기존 패턴 재사용, 원칙4). 별도 Pool 전용 DB 스키마를 새로 설계하지 않는다.
- **Web UI 인증**: **범위 밖**으로 확정. 단일 팀이 로컬에서 실행하는 것을 전제하며, 다중 사용자 인증·권한관리는 L5(조직 확장) 밖이다(§3 Out-of-scope와 일치).

이 세 결정은 Part IV의 ADR에서 공식적으로 재확인·기록된다 — 여기서의 확정은 저장소 부트스트랩을 진행하기 위한 실무적 가결정이며, `adr_review` 승인이 최종 확정이다.

## 11. 완료 정의 (Definition of Done)

Part XIII 회고(`docs/RETROSPECTIVE_T-D8D8CE.md`) 실측 대조 완료 — 각 항목의 정확한
근거·부분충족 사유는 그 문서 §1을 참고. 여기서는 최종 판정만 남긴다.

- [~] F1–F12 전부 골든셋 케이스로 검증됨 — 부분(F1-F4 완료, F5-F8은 계획 규모 미달로
      메커니즘만 검증, F9-F12는 SPEC이 애초에 골든셋 대상 밖으로 계획하고 수동 QA로 검증)
- [~] Gate A–G 7개 전부 최소 한 번 fail을 거쳐 `improve verify`로 confirmed 판정까지 완주 —
      부분(실제 fail한 A·C·D·F 중 A·C·D 완주, F는 별도 하네스 설계로 이 루프 대상 밖,
      B·E·G는 fail한 적이 없어 애초에 해당 없음)
- [~] 6개 승인 kind 전부 설계된 지점에서 실제 발동 — 부분(5/6, threshold_review만 계획대로
      발동하지 않음 — LIMITS L2)
- [x] 2인 팀 + 진짜 GitHub 원격에서 클레임 충돌 최소 1회 실전 발생·해소
- [x] Skills 3개+ 신규 발굴 및 `skill_merge` 승인
- [x] Pool 재사용률·Compose 성공률을 최종 회고(Part XIII)에서 정량 보고
