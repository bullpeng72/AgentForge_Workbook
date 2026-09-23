from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class AnthropicClient:
    """Tier 1(claude-sonnet-5, AC) 실제 호출 — ADR_T-D8D8CE.md 결정 2.

    ANTHROPIC_API_KEY가 없으면 생성 시점(또는 첫 호출 시점)에 실패한다 — 조용히
    폴백하지 않는다(원칙2: 실패는 실패로 보인다).
    """

    def __init__(self, model: str = "claude-sonnet-5") -> None:
        import anthropic

        self._client = anthropic.Anthropic()
        self._model = model

    def complete(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
