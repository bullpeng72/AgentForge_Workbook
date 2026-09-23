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
    """v2: 구문 검사(v0)에 더해, agents.yaml의 각 항목으로 실제 crewai.Agent 객체를
    생성해본다 — 구조적으로만 맞는 게 아니라 CrewAI가 실제로 받아들이는 필드인지까지
    확인한다(F4). crew.kickoff()(실제 실행)는 하지 않는다 — 이건 생성 대상 팀 자신의
    LLM 백엔드가 필요해 스코프 밖이다(SPEC §3 out-of-scope와 별개로, 생성-검증 단계와
    실제 실행 단계를 분리하는 것 자체가 이 프로젝트의 판단 — Verifier는 "구성 가능한가"만
    본다, "잘 작동하는가"는 안 본다)."""
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

    return VerificationResult(passed=not errors, errors=errors)


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
