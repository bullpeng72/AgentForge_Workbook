#!/usr/bin/env python3
"""전 구간 실제 검증 스크립트 — mock 없이 Tier1(GPT-5)+Tier2(Ollama qwen3-coder) 전부 실호출.

eval/smoke_v2.py가 Tier2만 실호출하던 것의 확장판 — OPENAI_API_KEY 확보 후(2026-09-23)
처음으로 전체 파이프라인을 mock 없이 돌린다. 브리프에 대한 도메인/역할 이름은 LLM이
자유롭게 정하므로, 골든셋의 expected_domain/expected_roles와 정확히 일치하지 않을 수
있다(v2까지의 mock 테스트와 다른 점 — 이건 결함이 아니라 실제 LLM의 자유도다). 이 스크립트는
"끝까지 도는가 + Verifier가 실제로 통과시키는가"만 확인한다. 정확한 도메인 분류/골든셋
일치율은 Part VII(Gate 정면돌파)의 Gate A 측정 대상이다.

사용법: python3 eval/smoke_full.py [golden_examples 파일 경로]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentforge.pipeline import run  # noqa: E402


def main() -> int:
    golden_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "data" / "golden_examples" / "v2_cases.json"
    )
    cases = json.loads(golden_path.read_text(encoding="utf-8"))

    failures = 0
    for case in cases:
        try:
            result = run(case["brief"])  # 클라이언트 전부 미지정 -> 전부 실제 호출
        except Exception as exc:  # noqa: BLE001 — 스모크 스크립트는 실패를 그대로 보고
            print(f"❌ {case['id']}: 파이프라인 예외 — {exc}")
            failures += 1
            continue

        status = "✅" if result.verification.passed else "❌"
        print(
            f"{status} {case['id']}: domain={result.golden_data.domain} "
            f"roles={result.team_design.roles} passed={result.verification.passed}"
        )
        if not result.verification.passed:
            for err in result.verification.errors:
                print(f"    - {err}")
            failures += 1

    print(f"\n{len(cases) - failures}/{len(cases)} passed (real GPT-5 + real Ollama, zero mocks)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
