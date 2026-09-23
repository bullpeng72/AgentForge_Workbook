from __future__ import annotations

from agentforge.code_generator.generator import GeneratedCode
from agentforge.spec_interpreter.interpreter import GoldenData
from agentforge.verifier.verifier import verify

_VALID_YAML = (
    "agents:\n"
    "  - name: Classifier\n"
    "    role: Classifier\n"
    '    goal: "분류를 수행한다"\n'
    '    backstory: "분류 담당 에이전트"\n'
    "    allow_delegation: false\n"
)
_VALID_CREW_PY = "from crewai import Agent, Task, Crew\n"


def test_verify_accepts_a_valid_agent_definition() -> None:
    generated = GeneratedCode(agents_yaml=_VALID_YAML, crew_py=_VALID_CREW_PY)
    golden_data = GoldenData(domain="support", goal="티켓 분류", success_criteria=["정확도 90% 이상"])
    result = verify(generated, golden_data)
    assert result.passed, result.errors


def test_verify_rejects_agent_missing_required_field() -> None:
    """v0의 구문검사는 이 케이스를 통과시켰을 것이다(YAML/Python 둘 다 문법상 유효) —
    v2가 새로 잡는 지점: CrewAI Agent가 실제로 요구하는 필드(backstory)가 빠졌다."""
    generated = GeneratedCode(
        agents_yaml=(
            "agents:\n"
            "  - name: Classifier\n"
            "    role: Classifier\n"
            '    goal: "분류를 수행한다"\n'
            # backstory 누락
        ),
        crew_py=_VALID_CREW_PY,
    )
    golden_data = GoldenData(domain="support", goal="티켓 분류", success_criteria=["정확도 90% 이상"])
    result = verify(generated, golden_data)
    assert not result.passed
    assert any("Classifier" in e for e in result.errors)


def test_verify_still_catches_syntax_errors_like_v0() -> None:
    generated = GeneratedCode(agents_yaml="agents: [", crew_py="def broken(:\n")
    golden_data = GoldenData(domain="support", goal="티켓 분류", success_criteria=["정확도 90% 이상"])
    result = verify(generated, golden_data)
    assert not result.passed
    assert any("파싱 실패" in e for e in result.errors)


def test_verify_builds_golden_set_from_success_criteria() -> None:
    """v3: agents.yaml/crew.py가 유효하면 success_criteria 각 항목이 골든 케이스가
    된다 — 추가 LLM 호출 없이 v1이 이미 뽑아둔 값을 재사용한다."""
    generated = GeneratedCode(agents_yaml=_VALID_YAML, crew_py=_VALID_CREW_PY)
    golden_data = GoldenData(
        domain="support",
        goal="티켓 분류",
        success_criteria=["정확도 90% 이상", "응답 지연 10초 이하"],
    )
    result = verify(generated, golden_data)
    assert result.passed
    assert result.golden_set == [
        {"id": "gc-1", "question": "티켓 분류", "criterion": "정확도 90% 이상"},
        {"id": "gc-2", "question": "티켓 분류", "criterion": "응답 지연 10초 이하"},
    ]
    assert result.eval_wiring_py is not None
    assert "@agent_eval" in result.eval_wiring_py
    assert "framework=\"crewai\"" in result.eval_wiring_py


def test_verify_fails_meta_check_when_success_criteria_is_empty() -> None:
    """원칙2: '골든셋을 만들었다'와 '그 골든셋이 쓸 만하다'는 다르다 — success_criteria가
    없으면 애초에 빈 골든셋이 나오고, 그건 통과가 아니라 실패다."""
    generated = GeneratedCode(agents_yaml=_VALID_YAML, crew_py=_VALID_CREW_PY)
    golden_data = GoldenData(domain="support", goal="티켓 분류", success_criteria=[])
    result = verify(generated, golden_data)
    assert not result.passed
    assert any("골든셋이 비어 있음" in e for e in result.errors)
    assert result.golden_set is None
