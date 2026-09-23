from __future__ import annotations

from dataclasses import dataclass

from agentforge.spec_interpreter.interpreter import GoldenData

_DOMAIN_TEMPLATES: dict[str, list[str]] = {
    "support": ["Classifier", "Responder"],
    "research": ["Researcher", "Writer"],
    "code_review": ["Reviewer"],
    "generic": ["Worker"],
}


@dataclass
class TeamDesign:
    domain: str
    roles: list[str]


def design(golden_data: GoldenData) -> TeamDesign:
    """v0: 도메인→역할목록 고정 템플릿 조회. LLM 없음(F2 스텁)."""
    roles = _DOMAIN_TEMPLATES.get(golden_data.domain, _DOMAIN_TEMPLATES["generic"])
    return TeamDesign(domain=golden_data.domain, roles=list(roles))
