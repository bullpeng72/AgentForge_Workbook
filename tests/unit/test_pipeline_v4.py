from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentforge.pipeline import run
from agentforge.pool.index import PoolIndex
from tests.unit.fakes import FakeLLMClient


@pytest.fixture
def pool(tmp_path: Path) -> PoolIndex:
    return PoolIndex(db_path=tmp_path / "pool.db")


def _interpreter_client(domain: str, goal: str) -> FakeLLMClient:
    return FakeLLMClient({"domain": domain, "goal": goal, "constraints": [], "success_criteria": [f"{domain} 완료"]})


def test_v4_first_run_generates_everything_and_populates_pool(pool: PoolIndex) -> None:
    """Pool이 비어 있으면 v3와 동일하게 전부 신규 생성하고, 성공하면 Pool에 채운다."""
    generator_client = FakeLLMClient(
        {
            "agents_yaml": (
                "agents:\n"
                "  - name: Classifier\n    role: Classifier\n    goal: \"분류\"\n    backstory: \"b\"\n"
                "  - name: Responder\n    role: Responder\n    goal: \"응답\"\n    backstory: \"b\"\n"
            ),
            "crew_py": "from crewai import Agent, Task, Crew\n",
        }
    )
    result = run(
        "고객 지원 티켓을 분류하고 응답하는 팀을 만들어줘",
        pool=pool,
        interpreter_client=_interpreter_client("support", "티켓 분류·응답"),
        designer_client=FakeLLMClient({"roles": ["Classifier", "Responder"]}),
        generator_client=generator_client,
    )

    assert result.verification.passed, result.verification.errors
    assert result.compose_result is not None
    assert result.compose_result.roles_to_generate == ["Classifier", "Responder"]

    pooled = pool.search_by_domain("support")
    assert {c.role for c in pooled} == {"Classifier", "Responder"}


def test_v4_second_run_reuses_from_pool_and_generates_only_the_gap(pool: PoolIndex) -> None:
    """같은 도메인에 두 번째로 다른 역할 조합(Classifier + Translator)이 오면,
    Classifier는 재사용하고 Translator만 새로 생성해야 한다(F8)."""
    # 1차 실행 — support 도메인에 Classifier를 채워 넣는다
    run(
        "고객 지원 티켓을 분류하는 에이전트를 만들어줘",
        pool=pool,
        interpreter_client=_interpreter_client("support", "티켓 분류"),
        designer_client=FakeLLMClient({"roles": ["Classifier"]}),
        generator_client=FakeLLMClient(
            {
                "agents_yaml": "agents:\n  - name: Classifier\n    role: Classifier\n    goal: \"분류\"\n    backstory: \"b\"\n",
                "crew_py": "from crewai import Agent\n",
            }
        ),
    )
    assert len(pool.search_by_domain("support")) == 1

    # 2차 실행 — Classifier는 재사용, Translator만 신규 생성돼야 한다
    generator_client_2 = FakeLLMClient(
        {
            "agents_yaml": "agents:\n  - name: Translator\n    role: Translator\n    goal: \"번역\"\n    backstory: \"b\"\n",
            "crew_py": "from crewai import Agent\n",
        }
    )
    result = run(
        "고객 지원 티켓을 분류하고 번역도 하는 팀을 만들어줘",
        pool=pool,
        interpreter_client=_interpreter_client("support", "티켓 분류·번역"),
        designer_client=FakeLLMClient({"roles": ["Classifier", "Translator"]}),
        generator_client=generator_client_2,
    )

    assert result.verification.passed, result.verification.errors
    assert result.compose_result.roles_to_generate == ["Translator"]  # Classifier는 재사용, 생성 안 함
    assert len(generator_client_2.prompts) == 1  # Translator 하나만 실제로 LLM 호출됨

    final_roles = {a["role"] for a in yaml.safe_load(result.generated.agents_yaml)["agents"]}
    assert final_roles == {"Classifier", "Translator"}  # 최종 결과물엔 둘 다 있어야 한다

    # Pool엔 이제 Classifier(1차) + Translator(2차) 둘 다 있어야 한다
    assert {c.role for c in pool.search_by_domain("support")} == {"Classifier", "Translator"}


def test_v4_without_pool_behaves_like_v3(pool: PoolIndex) -> None:
    """pool 인자를 안 주면 이전 버전과 동일하게 동작해야 한다(하위 호환)."""
    result = run(
        "코드 리뷰를 자동으로 해주는 에이전트를 만들어줘",
        interpreter_client=_interpreter_client("code_review", "코드 리뷰"),
        designer_client=FakeLLMClient({"roles": ["Reviewer"]}),
        generator_client=FakeLLMClient(
            {
                "agents_yaml": "agents:\n  - name: Reviewer\n    role: Reviewer\n    goal: \"리뷰\"\n    backstory: \"b\"\n",
                "crew_py": "from crewai import Agent\n",
            }
        ),
    )
    assert result.verification.passed
    assert result.compose_result is None
