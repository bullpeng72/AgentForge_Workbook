#!/usr/bin/env python3
"""v2 실제 검증 스크립트 — Code Generator만 진짜 Ollama(Tier2)를 호출한다.

Spec Interpreter·Team Designer는 여전히 mock이다(ANTHROPIC_API_KEY 미설정, Part VI
커밋 로그에 기록된 그대로). pytest 스위트에는 안 넣는다 — 실제 네트워크 호출은
Archivist 책의 관례대로 eval/ 스크립트가 담당하고 pytest는 오프라인으로 유지한다.

사용법: python3 eval/smoke_v2.py [golden_examples 파일 경로]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentforge.pipeline import run  # noqa: E402


class _FakeLLMClient:
    """tests/unit/fakes.py와 동일한 계약의 로컬 사본 — eval 스크립트가 tests/에
    의존하는 어색한 계층을 피하려고 여기서 따로 둔다."""

    def __init__(self, response: dict) -> None:
        self._response = response

    def complete(self, prompt: str) -> str:
        return json.dumps(self._response, ensure_ascii=False)


def main() -> int:
    golden_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "data" / "golden_examples" / "v2_cases.json"
    )
    cases = json.loads(golden_path.read_text(encoding="utf-8"))

    failures = 0
    for case in cases:
        interpreter_client = _FakeLLMClient(
            {
                "domain": case["expected_domain"],
                "goal": case["brief"],
                "constraints": [],
                "success_criteria": [f"{case['expected_domain']} 목표를 달성한다"],
            }
        )
        designer_client = _FakeLLMClient({"roles": case["expected_roles"]})
        # generator_client는 안 준다 -> OllamaClient가 실제로 호출된다(Tier2, qwen3-coder:latest)

        try:
            result = run(
                case["brief"],
                interpreter_client=interpreter_client,
                designer_client=designer_client,
            )
        except Exception as exc:  # noqa: BLE001 — 스모크 스크립트는 실패를 그대로 보고
            print(f"❌ {case['id']}: 파이프라인 예외 — {exc}")
            failures += 1
            continue

        status = "✅" if result.verification.passed else "❌"
        print(f"{status} {case['id']}: roles={result.team_design.roles} passed={result.verification.passed}")
        if not result.verification.passed:
            for err in result.verification.errors:
                print(f"    - {err}")
            failures += 1

    print(f"\n{len(cases) - failures}/{len(cases)} passed (real Ollama calls)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
