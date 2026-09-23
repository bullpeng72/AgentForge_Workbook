from __future__ import annotations

import ast
from dataclasses import dataclass, field

import yaml

from agentforge.code_generator.generator import GeneratedCode
from agentforge.spec_interpreter.interpreter import GoldenData

_EVAL_WIRING_TEMPLATE = '''"""자동 생성된 평가 배선 — AgentForge Verifier(v3)가 만들었다. 손으로 고치지 말 것."""
from agent_evaluator import PerformanceMonitor, agent_eval

monitor = PerformanceMonitor(output_dir="results/", agent_version="auto")


@agent_eval(monitor, framework="crewai", task_type="qa")
def run_crew(inputs: dict):
    from crew import crew  # 같은 디렉터리의 crew.py가 정의한 crew 인스턴스

    return crew.kickoff(inputs=inputs)
'''


@dataclass
class VerificationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    golden_set: list[dict] | None = None
    eval_wiring_py: str | None = None


def verify(generated: GeneratedCode, golden_data: GoldenData) -> VerificationResult:
    """v3: v2의 검증(구문+Agent 실제 생성)에 더해, 결과물(생성된 팀)을 평가할 골든셋과
    `@agent_eval` 배선 코드를 자동 생성한다(F4). golden_set은 Spec Interpreter가 이미
    뽑아둔 success_criteria에서 결정론적으로 합성한다 — 추가 LLM 호출 없음(비용·속도
    이유, 그리고 success_criteria 자체가 이미 v1에서 LLM이 만든 결과라 다시 LLM에
    물을 이유가 없다). 골든셋 자체가 비어있거나 구조가 이상하면(메타 검증) 실패로
    취급한다 — "골든셋을 만들었다"와 "그 골든셋이 쓸 만하다"는 다르다(원칙2)."""
    errors: list[str] = []

    try:
        parsed_yaml = yaml.safe_load(generated.agents_yaml)
    except yaml.YAMLError as exc:
        errors.append(f"agents.yaml 파싱 실패: {exc}")
        parsed_yaml = None

    try:
        ast.parse(generated.crew_py)
    except SyntaxError as exc:
        errors.append(f"crew.py 파싱 실패: {exc}")

    if parsed_yaml is not None:
        errors.extend(_verify_agents_instantiate(parsed_yaml))

    if errors:
        return VerificationResult(passed=False, errors=errors)

    golden_set = _build_golden_set(golden_data)
    errors.extend(_verify_golden_set(golden_set))
    eval_wiring_py = _EVAL_WIRING_TEMPLATE

    return VerificationResult(
        passed=not errors,
        errors=errors,
        golden_set=golden_set if not errors else None,
        eval_wiring_py=eval_wiring_py if not errors else None,
    )


def _verify_agents_instantiate(parsed_yaml: dict) -> list[str]:
    from crewai import Agent

    errors: list[str] = []
    agent_entries = parsed_yaml.get("agents", [])
    if not agent_entries:
        return ["agents.yaml에 'agents' 목록이 없거나 비어 있음"]

    for entry in agent_entries:
        try:
            Agent(
                role=entry["role"],
                goal=entry["goal"],
                backstory=entry["backstory"],
                allow_delegation=entry.get("allow_delegation", False),
            )
        except (KeyError, Exception) as exc:  # noqa: BLE001 — Agent 생성 실패는 전부 검증 실패로 취급
            errors.append(f"Agent 생성 실패({entry.get('name', '?')}): {exc}")

    return errors


def _build_golden_set(golden_data: GoldenData) -> list[dict]:
    """success_criteria 각 항목을 골든 케이스 하나로 취급한다 — 이미 v1에서 LLM이
    뽑아둔 결과를 재사용할 뿐, 새로 LLM을 호출하지 않는다."""
    return [
        {"id": f"gc-{i + 1}", "question": golden_data.goal, "criterion": criterion}
        for i, criterion in enumerate(golden_data.success_criteria)
    ]


def _verify_golden_set(golden_set: list[dict]) -> list[str]:
    """메타 검증 — 생성된 골든셋 자체가 쓸 만한지 확인한다(원칙2: 만들었다≠쓸 만하다)."""
    if not golden_set:
        return ["골든셋이 비어 있음 — success_criteria가 없는 Golden Data였을 가능성"]

    errors: list[str] = []
    for case in golden_set:
        if not case.get("question") or not case.get("criterion"):
            errors.append(f"골든셋 항목 {case.get('id', '?')}에 question 또는 criterion 누락")
    return errors
