from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentforge.pipeline import run

_GOLDEN_PATH = Path(__file__).resolve().parents[2] / "data" / "golden_examples" / "v0_cases.json"
_CASES = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_v0_pipeline_matches_golden_case(case: dict) -> None:
    result = run(case["brief"])

    assert result.golden_data.domain == case["expected_domain"]
    assert result.team_design.roles == case["expected_roles"]
    assert result.verification.passed, result.verification.errors


def test_v0_pipeline_is_deterministic() -> None:
    brief = _CASES[0]["brief"]
    first = run(brief)
    second = run(brief)
    assert first.team_design.roles == second.team_design.roles
    assert first.generated.agents_yaml == second.generated.agents_yaml
