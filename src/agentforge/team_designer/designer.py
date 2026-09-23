from __future__ import annotations

import json
from dataclasses import dataclass

from agentforge.llm.client import LLMClient, OpenAIClient
from agentforge.spec_interpreter.interpreter import GoldenData

_PROMPT = """다음은 확정된 Golden Data다:

도메인: {domain}
목표: {goal}
제약: {constraints}
성공기준: {success_criteria}

이 목표를 달성할 CrewAI 에이전트 팀의 역할을 설계하라. 역할은 2개를 넘지 않게 하고,
각 역할 이름은 영문 PascalCase 한 단어로 하라. 아래 JSON 스키마로만 응답하라:
{{"roles": ["<역할1>", "<역할2, 선택>"]}}"""


@dataclass
class TeamDesign:
    domain: str
    roles: list[str]


def design(golden_data: GoldenData, client: LLMClient | None = None) -> TeamDesign:
    """v1: Tier 1 LLM으로 역할분담을 설계한다(F2).

    client를 안 주면 OpenAIClient를 지연 생성한다 — API 키가 없으면 여기서 실패한다.
    """
    client = client or OpenAIClient()
    prompt = _PROMPT.format(
        domain=golden_data.domain,
        goal=golden_data.goal,
        constraints=golden_data.constraints,
        success_criteria=golden_data.success_criteria,
    )
    raw = client.complete(prompt)
    data = json.loads(raw)
    return TeamDesign(domain=golden_data.domain, roles=data["roles"])
