from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentforge.pipeline import run
from tests.unit.fakes import FakeLLMClient

_GOLDEN_PATH = Path(__file__).resolve().parents[2] / "data" / "golden_examples" / "v0_cases.json"
_CASES = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))


def _clients_for(case: dict) -> tuple[FakeLLMClient, FakeLLMClient]:
    interpreter_client = FakeLLMClient(
        {
            "domain": case["expected_domain"],
            "goal": case["brief"],
            "constraints": [],
            "success_criteria": [],
        }
    )
    designer_client = FakeLLMClient({"roles": case["expected_roles"]})
    return interpreter_client, designer_client


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_v1_pipeline_with_mocked_llm(case: dict) -> None:
    """v1: Spec Interpreter·Team Designer가 LLM 응답을 올바르게 파싱해 파이프라인이
    끝까지 도는지 확인한다(실제 API 호출 없음 — ANTHROPIC_API_KEY 미설정 상태에서 검증)."""
    interpreter_client, designer_client = _clients_for(case)

    result = run(
        case["brief"],
        interpreter_client=interpreter_client,
        designer_client=designer_client,
    )

    assert result.golden_data.domain == case["expected_domain"]
    assert result.team_design.roles == case["expected_roles"]
    assert result.verification.passed, result.verification.errors
    assert len(interpreter_client.prompts) == 1
    assert len(designer_client.prompts) == 1


def test_v1_pipeline_is_deterministic_given_the_same_llm_output() -> None:
    case = _CASES[0]
    interpreter_client_1, designer_client_1 = _clients_for(case)
    first = run(case["brief"], interpreter_client=interpreter_client_1, designer_client=designer_client_1)

    interpreter_client_2, designer_client_2 = _clients_for(case)
    second = run(case["brief"], interpreter_client=interpreter_client_2, designer_client=designer_client_2)

    assert first.team_design.roles == second.team_design.roles
    assert first.generated.agents_yaml == second.generated.agents_yaml
