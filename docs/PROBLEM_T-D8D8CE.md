# AgentForge v0-v5 (T-D8D8CE)

## 무엇을

자연어 브리프 하나를 받아 실행 가능한 CrewAI 멀티에이전트 팀(코드+평가 스캐폴드)을 생성하고,
이미 만든 에이전트를 Pool에 쌓아 재사용하며, 이 전 과정을 Web UI로 조작할 수 있는 도구
**AgentForge**를 만든다. 상세 기능/비기능 요구사항은 `docs/SPEC.md`가 정본이다.

## 왜

멀티에이전트 조율(Gate F)을 진짜로 실측하고, Harness Autopilot의 6개 승인 kind 전부를
설계 단계부터 겨냥해 실제로 발동시키고, Skills를 시작부터 활용 계획에 포함시키는 과제가
필요하다 — 이 세 가지를 전부 충족하려면 협업 컴포넌트가 여럿이고 팀 규모가 실전에
가까운 과제가 필요하다. AgentForge는 이걸 설계 단계부터 반영한다 — 진짜 멀티에이전트,
6개 승인 kind 전부 설계상 발동, Skills 실제 발굴까지.

외부 조사(2026-09)로 CAAS·`multi-agent-generator`(PyPI) 같은 동일 범주 도구가 이미 존재함을
확인했다 — 시장 경쟁력이 아니라 **방법론 교재**로서의 가치가 이 과제의 목적이다.

## 성공 기준

`docs/SPEC.md` §11(완료 정의) 참고 — 요약하면: F1–F12 전부 골든셋 검증, Gate A–G 7개 전부
fail→진단→confirmed 완주, 6개 승인 kind 전부 설계된 지점에서 실제 발동, 2인+ 팀 클레임 충돌
실전 해소, Skills 3개+ 신규 발굴.

## 제약

- 출력 프레임워크는 CrewAI 하나만(스코프 폭발 방지)
- Tier 1(분석·설계)은 AC, Tier 2(반복 실행)는 AOO — 원칙5에 따른 혼합 사용
- Web UI는 FastAPI+Jinja2로 한정(Autopilot 대시보드 패턴 재사용, 새 프런트엔드 스택 도입 안 함)

## 범위 밖

- LangGraph·Agno·ReAct 등 타 프레임워크 출력(`multi-agent-generator`가 이미 하는 영역)
- 크로스팀·크로스프로젝트 Pool 공유(포트폴리오 단위)
- 프로덕션 멀티테넌시·과금
- Web UI 인증/권한관리(단일 팀 로컬 실행 전제)
