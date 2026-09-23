from __future__ import annotations

from dataclasses import dataclass, field

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "support": ["고객", "지원", "티켓", "문의"],
    "research": ["리서치", "보고서", "조사", "자료"],
    "code_review": ["코드", "리뷰", "검토"],
}


@dataclass
class GoldenData:
    domain: str
    goal: str
    constraints: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)


def interpret(brief: str) -> GoldenData:
    """v0: 키워드 매칭으로 브리프를 Golden Data로 변환한다. LLM 없음(F1 스텁)."""
    matched_domain = "generic"
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(kw in brief for kw in keywords):
            matched_domain = domain
            break

    return GoldenData(
        domain=matched_domain,
        goal=brief.strip(),
        constraints=[],
        success_criteria=[f"{matched_domain} 도메인 팀이 생성된다"],
    )
