# AgentForge — 《AgentForge 실습서》 동봉 저장소

《AgentForge 실습서》를 따라 하기 위한 러닝 예제다. 자연어 브리프 하나를 받아 실행 가능한
CrewAI 멀티에이전트 팀(코드+평가 스캐폴드)을 생성하고, 이미 만든 에이전트를 Pool에 쌓아
재사용하며, 전 과정을 Web UI로 조작할 수 있는 도구 **AgentForge**를 하네스 방법론 +
AOO/AC 혼합 + Harness Autopilot + Skills로 처음부터 끝까지 만든다.

이 저장소는 책의 각 Part를 따라가며 자란다 — **현재 Part I(준비) 착수 전 상태**.

## 빠른 시작

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## 구조

```
src/agentforge/     # spec_interpreter/team_designer/code_generator/verifier/composer
data/                # golden_examples
docs/                # SPEC.md(정본) 등
.opencode/skills/    # Autopilot install로 채워짐
.aoo/                 # Autopilot 운영 데이터(Part I에서 생성)
results/             # 평가 결과(final/만 커밋, 나머지는 gitignore)
tests/{unit,integration}/
eval/                # 하네스 스크립트
```

## 라이선스

MIT
