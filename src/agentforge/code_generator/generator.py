from __future__ import annotations

import json
from dataclasses import dataclass

from agentforge.llm.client import LLMClient, OllamaClient
from agentforge.team_designer.designer import TeamDesign

_PROMPT = """역할 목록: {roles!r}

이 역할들로 CrewAI agents.yaml과 crew.py를 만들어라. 아래 JSON 스키마로만 응답하라
(다른 텍스트 없이, 마크다운 코드펜스 없이):
{{"agents_yaml": "<YAML 문자열>", "crew_py": "<Python 문자열, from crewai import Agent 로 시작>"}}"""


@dataclass
class GeneratedCode:
    agents_yaml: str
    crew_py: str


def generate(team_design: TeamDesign, client: LLMClient | None = None) -> GeneratedCode:
    """v2: Tier 2 LLM(로컬 Ollama)으로 실제 CrewAI 코드를 합성한다(F3).

    client를 안 주면 OllamaClient를 지연 생성한다 — 서버가 안 떠 있으면 여기서 실패한다.
    """
    client = client or OllamaClient()
    raw = client.complete(_PROMPT.format(roles=team_design.roles))
    data = json.loads(raw)
    return GeneratedCode(agents_yaml=data["agents_yaml"], crew_py=data["crew_py"])
