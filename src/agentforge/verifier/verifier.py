from __future__ import annotations

import ast
from dataclasses import dataclass, field

import yaml

from agentforge.code_generator.generator import GeneratedCode


@dataclass
class VerificationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)


def verify(generated: GeneratedCode) -> VerificationResult:
    """v0: 생성 코드가 구문적으로 유효한지만 확인한다. smoke-test 실행은 v2(Part VI)부터(F4 스텁)."""
    errors: list[str] = []

    try:
        yaml.safe_load(generated.agents_yaml)
    except yaml.YAMLError as exc:
        errors.append(f"agents.yaml 파싱 실패: {exc}")

    try:
        ast.parse(generated.crew_py)
    except SyntaxError as exc:
        errors.append(f"crew.py 파싱 실패: {exc}")

    return VerificationResult(passed=not errors, errors=errors)
