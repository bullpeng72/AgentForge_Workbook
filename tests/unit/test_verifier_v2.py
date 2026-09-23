from __future__ import annotations

from agentforge.code_generator.generator import GeneratedCode
from agentforge.verifier.verifier import verify


def test_verify_accepts_a_valid_agent_definition() -> None:
    generated = GeneratedCode(
        agents_yaml=(
            "agents:\n"
            "  - name: Classifier\n"
            "    role: Classifier\n"
            '    goal: "분류를 수행한다"\n'
            '    backstory: "분류 담당 에이전트"\n'
            "    allow_delegation: false\n"
        ),
        crew_py="from crewai import Agent, Task, Crew\n",
    )
    result = verify(generated)
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
        crew_py="from crewai import Agent, Task, Crew\n",
    )
    result = verify(generated)
    assert not result.passed
    assert any("Classifier" in e for e in result.errors)


def test_verify_still_catches_syntax_errors_like_v0() -> None:
    generated = GeneratedCode(agents_yaml="agents: [", crew_py="def broken(:\n")
    result = verify(generated)
    assert not result.passed
    assert any("파싱 실패" in e for e in result.errors)
