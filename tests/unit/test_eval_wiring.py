from __future__ import annotations

from agentforge.code_generator.generator import GeneratedCode
from agentforge.eval_wiring import _build_agent_interactions, _build_tool_calls, _detect_frameworks
from agentforge.pipeline import PipelineResult
from agentforge.spec_interpreter.interpreter import GoldenData
from agentforge.team_designer.designer import TeamDesign
from agentforge.verifier.verifier import VerificationResult

_GOLDEN_DATA = GoldenData(domain="support", goal="티켓 분류", success_criteria=["정확도 90%"])
_TEAM_DESIGN = TeamDesign(domain="support", roles=["Classifier", "Responder"])


def _result_with(agents_yaml: str, crew_py: str) -> PipelineResult:
    return PipelineResult(
        golden_data=_GOLDEN_DATA,
        team_design=_TEAM_DESIGN,
        generated=GeneratedCode(agents_yaml=agents_yaml, crew_py=crew_py),
        verification=VerificationResult(passed=True),
    )


def test_detect_frameworks_finds_only_crewai_in_clean_code() -> None:
    assert _detect_frameworks("from crewai import Agent, Task, Crew\n") == ["crewai"]


def test_detect_frameworks_flags_out_of_scope_import() -> None:
    """Gate B — SPEC §3은 CrewAI 하나만 허용한다."""
    code = "from crewai import Agent\nfrom langgraph.graph import StateGraph\n"
    assert _detect_frameworks(code) == ["crewai", "langgraph"]


def test_build_tool_calls_matches_detected_frameworks() -> None:
    result = _result_with("agents:\n  - name: X\n    role: X\n", "from crewai import Agent\n")
    assert _build_tool_calls(result) == [{"tool": "framework:crewai"}]


def test_build_agent_interactions_marks_role_match_as_success() -> None:
    yaml_with_both_roles = (
        "agents:\n  - name: Classifier\n    role: Classifier\n  - name: Responder\n    role: Responder\n"
    )
    result = _result_with(yaml_with_both_roles, "from crewai import Agent\n")
    interactions = _build_agent_interactions(result)
    assert all(i["success"] for i in interactions)
    assert {i["context"]["role"] for i in interactions} == {"Classifier", "Responder"}


def test_build_agent_interactions_marks_missing_role_as_failure() -> None:
    """Gate F — Team Designer가 정한 역할을 Code Generator가 빠뜨리면 설계-구현
    불일치로 잡혀야 한다(ADR 결정 2)."""
    yaml_missing_responder = "agents:\n  - name: Classifier\n    role: Classifier\n"
    result = _result_with(yaml_missing_responder, "from crewai import Agent\n")
    interactions = _build_agent_interactions(result)
    by_role = {i["context"]["role"]: i["success"] for i in interactions}
    assert by_role == {"Classifier": True, "Responder": False}


def test_build_agent_interactions_survives_non_dict_yaml() -> None:
    """실측 회귀 테스트(v2-04-ambiguous, gate_run_4) — verifier.py와 같은 버그가
    여기도 있었다: agents_yaml이 dict가 아닌 값으로 파싱되면 AttributeError."""
    result = _result_with("이건 그냥 문자열이다", "from crewai import Agent\n")
    interactions = _build_agent_interactions(result)  # AttributeError 없이 끝나야 한다
    assert all(not i["success"] for i in interactions)
