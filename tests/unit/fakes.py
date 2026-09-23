from __future__ import annotations

import json


class FakeLLMClient:
    """테스트용 LLMClient — 실제 API 호출 없음. dict를 주면 JSON으로 직렬화해 반환하고,
    str을 주면 그대로 반환한다(형식 오류 케이스 재현용)."""

    def __init__(self, response: dict | str) -> None:
        self._response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self._response, str):
            return self._response
        return json.dumps(self._response, ensure_ascii=False)
