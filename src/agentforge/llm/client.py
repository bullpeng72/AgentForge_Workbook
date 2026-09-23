from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class AnthropicClient:
    """Tier 1 후보 A(claude-sonnet-5, AC) — ADR_T-D8D8CE.md 결정 2 개정 이력 참고.

    ANTHROPIC_API_KEY가 없으면 생성 시점(또는 첫 호출 시점)에 실패한다 — 조용히
    폴백하지 않는다(원칙2: 실패는 실패로 보인다). 현재 Tier 1 기본값은 OpenAIClient —
    이 클래스는 대체 프로바이더로 남겨둔다(LLMClient 프로토콜만 맞으면 교체 가능).
    """

    def __init__(self, model: str = "claude-sonnet-5") -> None:
        import anthropic

        self._client = anthropic.Anthropic()
        self._model = model

    def complete(self, prompt: str) -> str:
        from anthropic.types import TextBlock

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        block = response.content[0]
        if not isinstance(block, TextBlock):
            # 원칙2: 조용히 폴백하지 않는다 — 텍스트가 아닌 블록(thinking/tool_use 등)이
            # 오면 그 자리에서 실패로 드러낸다.
            raise RuntimeError(f"expected a text content block, got {type(block).__name__}")
        return block.text


class OpenAIClient:
    """Tier 1(GPT, AC) 실제 호출 — ADR_T-D8D8CE.md 결정 2 개정(Part VI, Anthropic 키
    미확보로 실전 검증이 막혀 프로바이더 전환).

    OPENAI_API_KEY가 없으면 생성 시점(또는 첫 호출 시점)에 실패한다 — 조용히
    폴백하지 않는다(원칙2: 실패는 실패로 보인다).

    Gate C/F 재현성 조치(recommend_fix 참조, Part VII): models.lock이 seed=42를
    선언해놓고 실제로는 아무 파라미터도 안 넘기고 있었다 — 그 계약을 이제 지킨다.
    `temperature=0`은 실측으로 거부됨을 확인했다(gpt-5는 기본값 1만 허용, 400 에러:
    "temperature does not support 0 with this model") — reasoning 모델의 제약이라
    강제하지 않는다. seed만으로는 완전한 결정성을 보장 못한다(OpenAI 문서상 "best
    effort") — 재현성이 여전히 낮으면 이게 한계다.
    """

    def __init__(self, model: str = "gpt-5", seed: int = 42) -> None:
        import openai

        self._client = openai.OpenAI()
        self._model = model
        self._seed = seed

    def complete(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            seed=self._seed,
        )
        content = response.choices[0].message.content
        if content is None:
            # 원칙2: 조용히 폴백하지 않는다 — 텍스트가 없는 응답(예: tool-call만 온 경우)은
            # 그 자리에서 실패로 드러낸다.
            raise RuntimeError("OpenAI response had no text content")
        return content


class OllamaClient:
    """Tier 2(qwen3-coder:latest, AOO) 실제 호출 — ADR_T-D8D8CE.md 결정 2.

    Anthropic과 달리 API 키가 필요 없다 — 로컬 Ollama 서버(기본 11434)에 직접 요청한다.
    서버가 안 떠 있으면 requests.RequestException이 그대로 올라간다(조용히 폴백 안 함).

    Gate C/F 재현성 조치(Part VII): OllamaClient와 달리 이쪽은 `temperature=0`이
    실측으로 허용됨을 확인했다(reasoning 모델이 아니라서 OpenAI의 제약이 없다) —
    seed와 함께 둘 다 넘긴다. models.lock의 seed=42 계약을 여기서도 지킨다.
    """

    def __init__(
        self,
        model: str = "qwen3-coder:latest",
        host: str = "http://localhost:11434",
        timeout: float = 120.0,
        seed: int = 42,
        temperature: float = 0.0,
    ) -> None:
        self._model = model
        self._host = host
        self._timeout = timeout
        self._seed = seed
        self._temperature = temperature

    def complete(self, prompt: str) -> str:
        import requests

        response = requests.post(
            f"{self._host}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"seed": self._seed, "temperature": self._temperature},
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()["response"]
