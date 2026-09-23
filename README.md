# AgentForge — 《AgentForge 실습서》 동봉 저장소

《AgentForge 실습서》를 따라 하기 위한 러닝 예제다. 자연어 브리프 하나를 받아 실행 가능한
CrewAI 멀티에이전트 팀(코드+평가 스캐폴드)을 생성하고, 이미 만든 에이전트를 Pool에 쌓아
재사용하며, 전 과정을 Web UI로 조작할 수 있는 도구 **AgentForge**를 하네스 방법론 +
AOO/AC 혼합 + Harness Autopilot + Skills로 처음부터 끝까지 만든다.

이 저장소는 책의 각 Part를 따라가며 자랐다 — **v0-v5 전 버전 구현·실측 완료, 릴리스
승인(`release_hold`) 완료**(`.aoo/tasks/T-D8D8CE.json` phase 7 · `docs/RELEASE_HOLD_T-D8D8CE.md`).
마일스톤 태그: `s0-setup` → `spec-approved` → `design-approved` → `v0-baseline` →
`v2-real-codegen` → `v3-self-eval` → `team-ci-ready` → `phase6-skills` →
`v4-pool-compose` → `v5-webui` → `release-hold-approved`.

**알려진 갭을 숨기지 않는다** — Gate D(성능계약)·F(멀티에이전트조율)는 0.7 기준 미달(warn)로
릴리스됐고, v4(Pool)는 Gate 점수 기준 회귀 테스트 커버리지가 없다. 전부
`docs/LIMITS_T-D8D8CE.md`에 기록돼 있다. 이 저장소의 목적은 완벽한 점수가 아니라 Harness
Gate 마찰을 정직하게 보여주는 것이다.

## 빠른 시작

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/unit/ -q               # 오프라인 단위 테스트(LLM 호출 없음)
agentforge-webui                    # Web UI — http://127.0.0.1:8767
```

실 API 호출을 쓰는 배치 실행은 `eval/*.py`를 직접 돌린다(`.env`에 `OPENAI_API_KEY` 필요,
Tier2는 로컬 Ollama `qwen3-coder`):

```bash
python eval/run_batch.py        # 골든셋 8건 전체 실행
python eval/run_pool_batch.py   # Pool 재사용(F5-F8) 실측 하네스
```

## 구조

```
src/agentforge/
  spec_interpreter/  team_designer/  code_generator/  verifier/   # v0-v3
  pool/               # AgentContract·PoolIndex(SQLite)·Composer·gate_lookup — v4
  webui/              # FastAPI Web UI(Pool 브라우저·팀 구성·평가 결과·승인 현황) — v5
  pipeline.py         # 전체 파이프라인 조립(pool= 유무로 v3/v4 분기)
  eval_wiring.py      # @agent_eval 배선(Gate A-G)
data/golden_examples/  # 버전별 골든셋(v2·v4)
docs/                  # SPEC.md(정본)·ADR·LIMITS·RELEASE_HOLD 등
.claude/skills/        # Autopilot install로 채워짐 + 이 프로젝트에서 발굴한 3종
.aoo/                  # Autopilot 운영 데이터(과제·팀·승인·클레임·결정 원장·실험)
results/                # 평가 결과(final/만 커밋, 나머지는 gitignore)
tests/unit/             # 오프라인 단위 테스트(FakeLLMClient, 51건)
eval/                   # 실 API 호출 하네스 스크립트
```

## 라이선스

MIT
