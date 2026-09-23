from __future__ import annotations

import json

import pytest

from agentforge.spec_interpreter.interpreter import interpret
from tests.unit.fakes import FakeLLMClient


def test_interpret_parses_well_formed_response() -> None:
    client = FakeLLMClient(
        {"domain": "support", "goal": "티켓 분류", "constraints": ["PII 마스킹"], "success_criteria": ["정확도 90%"]}
    )
    data = interpret("고객 지원 티켓을 분류해줘", client=client)
    assert data.domain == "support"
    assert data.constraints == ["PII 마스킹"]


def test_interpret_raises_on_malformed_json() -> None:
    """SPEC.md §6 '모호한 브리프 파싱 실패' — 형식이 깨진 응답을 조용히 무시하지 않고
    그대로 실패시킨다(AnthropicClient 독스트링의 원칙2 주장을 실제로 검증)."""
    client = FakeLLMClient("이건 JSON이 아니라 그냥 문장이다")
    with pytest.raises(json.JSONDecodeError):
        interpret("아무 브리프", client=client)
