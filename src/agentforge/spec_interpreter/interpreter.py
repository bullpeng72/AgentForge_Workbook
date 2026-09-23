from __future__ import annotations

import json
from dataclasses import dataclass, field

from agentforge.llm.client import AnthropicClient, LLMClient

_PROMPT = """다음은 새 에이전트 팀을 요청하는 자연어 브리프다:

{brief}

이 브리프를 분석해 아래 JSON 스키마로만 응답하라(다른 텍스트 없이):
{{"domain": "<한 단어, 예: support/research/code_review/generic>", "goal": "<목표 한 문장>", "constraints": ["<제약1>", "..."], "success_criteria": ["<성공기준1>", "..."]}}"""


@dataclass
class GoldenData:
    domain: str
    goal: str
    constraints: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)


def interpret(brief: str, client: LLMClient | None = None) -> GoldenData:
    """v1: Tier 1 LLM으로 브리프를 Golden Data로 변환한다(F1).

    client를 안 주면 AnthropicClient를 지연 생성한다 — API 키가 없으면 여기서 실패한다.
    """
    client = client or AnthropicClient()
    raw = client.complete(_PROMPT.format(brief=brief))
    data = json.loads(raw)
    return GoldenData(
        domain=data["domain"],
        goal=data["goal"],
        constraints=data.get("constraints", []),
        success_criteria=data.get("success_criteria", []),
    )
