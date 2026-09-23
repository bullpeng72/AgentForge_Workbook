# AgentForge — 자주 쓰는 명령 모음.
# 부록 D를 쓰며 처음 만들었다 — Part I-XIII 전체는 이 파일 없이 raw 명령으로 진행됐다
# (AOO_Autopilot_Workbook 부록 A와 같은 사정: "쓸 스크립트가 생기면 추가한다"고 미뤄둔 채
# 끝까지 손으로 쳐 왔다). 아래 각 타깃은 책 본문에서 실제로 쓰인 raw 명령 그대로다 —
# 새 동작을 추가하지 않았다.

# 오프라인 단위 테스트(LLM 호출 없음, Part V-XI 전체가 이걸로 검증됨)
test:
    pytest tests/unit/ -v

# 커밋된 baseline으로 정적 Gate 검사(Part VIII Ch34 — CI의 gate 잡과 동일)
gate:
    agent-eval gate results/final/baseline.json --tcr 85

# 클레임 감사(Part VIII Ch32-33)
claims-audit:
    agent-eval claims audit --ttl-hours 8

# Autopilot 과제 상태(Part 전체에서 반복 확인)
show-task:
    agent-eval autopilot show-task T-D8D8CE

# 결정 원장 조회(Part XII Ch49)
decisions:
    agent-eval decisions list .aoo/decisions.jsonl

# Web UI(Part XI) — http://127.0.0.1:8767
webui:
    agentforge-webui

# 골든셋 8건 전체 실행 — 실 API 필요(Part VII, .env에 OPENAI_API_KEY 필요)
eval-batch:
    python eval/run_batch.py

# Pool 재사용 실측 하네스 — 실 API 필요(Part X Ch42)
eval-pool:
    python eval/run_pool_batch.py

# 개발 환경 헬스체크 — venv 활성 여부, SDK 버전, Ollama 응답
doctor:
    python3 -c "import sys; print('python', sys.version.split()[0])"
    agent-eval --version
    ollama list | head -5 || echo "Ollama 응답 없음 — Tier2(qwen3-coder) 호출 불가"
