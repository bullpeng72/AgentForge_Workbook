from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentforge.pipeline import run
from tests.unit.fakes import FakeLLMClient

_GOLDEN_PATH = Path(__file__).resolve().parents[2] / "data" / "golden_examples" / "v2_cases.json"
_CASES = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))


def _generated_code_for(roles: list[str]) -> dict:
    agents = [
        {
            "name": role,
            "role": role,
            "goal": f"{role}의 역할을 수행한다",
            "backstory": f"{role} 스텁 backstory",
        }
        for role in roles
    ]
    yaml_body = "agents:\n" + "".join(
        f"  - name: {a['name']}\n    role: {a['role']}\n    goal: \"{a['goal']}\"\n"
        f"    backstory: \"{a['backstory']}\"\n    allow_delegation: false\n"
        for a in agents
    )
    return {"agents_yaml": yaml_body, "crew_py": f"from crewai import Agent, Task, Crew\n\nROLES = {roles!r}\n"}


def _clients_for(case: dict) -> tuple[FakeLLMClient, FakeLLMClient, FakeLLMClient]:
    interpreter_client = FakeLLMClient(
        {
            "domain": case["expected_domain"],
            "goal": case["brief"],
            "constraints": [],
            "success_criteria": [f"{case['expected_domain']} 목표를 달성한다"],
        }
    )
    designer_client = FakeLLMClient({"roles": case["expected_roles"]})
    generator_client = FakeLLMClient(_generated_code_for(case["expected_roles"]))
    return interpreter_client, designer_client, generator_client


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_v3_pipeline_with_mocked_llm(case: dict) -> None:
    """v3: 배선(v1)·Agent 실제 생성(v2)에 더해 결과물용 골든셋+eval 배선 자동생성까지
    확인한다. 실제 GPT-5/Ollama 호출 검증은 eval/smoke_full.py가 별도로 한다."""
    interpreter_client, designer_client, generator_client = _clients_for(case)

    result = run(
        case["brief"],
        interpreter_client=interpreter_client,
        designer_client=designer_client,
        generator_client=generator_client,
    )

    assert result.golden_data.domain == case["expected_domain"]
    assert result.team_design.roles == case["expected_roles"]
    assert result.verification.passed, result.verification.errors
    assert result.verification.golden_set
    assert result.verification.eval_wiring_py is not None
    assert "@agent_eval" in result.verification.eval_wiring_py


def test_v3_pipeline_is_deterministic_given_the_same_llm_output() -> None:
    case = _CASES[0]
    first = run(case["brief"], **dict(zip(
        ("interpreter_client", "designer_client", "generator_client"), _clients_for(case)
    )))
    second = run(case["brief"], **dict(zip(
        ("interpreter_client", "designer_client", "generator_client"), _clients_for(case)
    )))
    assert first.team_design.roles == second.team_design.roles
    assert first.generated.agents_yaml == second.generated.agents_yaml
    assert first.verification.golden_set == second.verification.golden_set
