from __future__ import annotations

from dataclasses import dataclass

from agentforge.team_designer.designer import TeamDesign

_AGENTS_YAML_TEMPLATE = """{role_entries}"""
_AGENT_ENTRY_TEMPLATE = """{slug}:
  role: {role}
  goal: {role}의 역할을 수행한다
  backstory: v0 스텁 — 실제 backstory는 v1(Part VI)에서 채운다
"""

_CREW_PY_TEMPLATE = '''"""v0 스텁 — 실제 CrewAI Crew 조립은 v2(Part VI)에서 채운다."""

ROLES = {roles!r}
'''


@dataclass
class GeneratedCode:
    agents_yaml: str
    crew_py: str


def generate(team_design: TeamDesign) -> GeneratedCode:
    """v0: 역할목록을 고정 문자열 템플릿에 채워 넣는다. 실제 코드 합성 없음(F3 스텁)."""
    entries = "\n".join(
        _AGENT_ENTRY_TEMPLATE.format(slug=role.lower(), role=role)
        for role in team_design.roles
    )
    agents_yaml = _AGENTS_YAML_TEMPLATE.format(role_entries=entries)
    crew_py = _CREW_PY_TEMPLATE.format(roles=team_design.roles)
    return GeneratedCode(agents_yaml=agents_yaml, crew_py=crew_py)
