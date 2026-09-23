from __future__ import annotations

from pathlib import Path

import pytest

from agentforge.pool.composer import compose
from agentforge.pool.contract import AgentContract
from agentforge.pool.index import PoolIndex


@pytest.fixture
def pool(tmp_path: Path) -> PoolIndex:
    return PoolIndex(db_path=tmp_path / "pool.db")


def _contract(role: str, domain: str, output: str, task_id: str) -> AgentContract:
    return AgentContract(
        role=role,
        domain=domain,
        input_description=f"{domain} 관련 브리프",
        output_description=output,
        source_task_id=task_id,
        agents_yaml_snippet=f"agents:\n  - name: {role}\n    role: {role}\n",
    )


def test_pool_index_add_and_search_roundtrip(pool: PoolIndex) -> None:
    c = _contract("Classifier", "support", "티켓을 분류한다", "task_1")
    pool.add(c)
    results = pool.search_by_domain("support")
    assert len(results) == 1
    assert results[0].role == "Classifier"


def test_compose_reuses_exact_match(pool: PoolIndex) -> None:
    pool.add(_contract("Classifier", "support", "티켓을 분류한다", "task_1"))
    result = compose(domain="support", roles=["Classifier"], pool=pool)
    assert result.decisions[0].action == "reuse_exact"
    assert result.roles_to_generate == []


def test_compose_auto_adapts_compatible_near_match(pool: PoolIndex) -> None:
    """새 역할명(Reviewer)의 단어가 기존 계약의 output_description에 있으면(리뷰)
    자동 어댑터로 재사용한다."""
    pool.add(_contract("Classifier", "support", "티켓을 분류하고 review 결과를 남긴다", "task_1"))
    result = compose(domain="support", roles=["Reviewer"], pool=pool)
    decision = result.decisions[0]
    assert decision.action == "reuse_adapted"
    assert decision.adapted_agents_yaml_snippet is not None
    assert "Reviewer" in decision.adapted_agents_yaml_snippet
    assert result.roles_to_generate == []


def test_compose_flags_for_human_when_incompatible(pool: PoolIndex) -> None:
    """같은 도메인에 후보는 있지만 역할명이 output_description과 전혀 안 겹치면
    자동 재사용을 거부하고 사람에게 넘긴다."""
    pool.add(_contract("Classifier", "support", "티켓을 분류한다", "task_1"))
    result = compose(domain="support", roles=["LegalReviewer"], pool=pool)
    decision = result.decisions[0]
    assert decision.action == "flag_for_human"
    assert result.roles_to_generate == ["LegalReviewer"]


def test_compose_generates_new_when_domain_has_no_candidates(pool: PoolIndex) -> None:
    result = compose(domain="translation", roles=["Translator"], pool=pool)
    decision = result.decisions[0]
    assert decision.action == "generate_new"
    assert result.roles_to_generate == ["Translator"]


def test_compose_checks_all_domain_candidates_not_just_first(pool: PoolIndex) -> None:
    """실측(gate_run_pool, Part X) 회귀 테스트 — 필요한 역할이 도메인의 '첫' 후보와는
    안 맞고 '두 번째' 후보와만 맞으면, 이전엔 flag_for_human으로 새버렸다(첫 후보만
    보던 버그). 전 후보를 훑어 호환되는 걸 찾아야 한다."""
    pool.add(_contract("Sanitizer", "support", "입력을 정제한다", "task_1"))
    pool.add(_contract("Classifier", "support", "티켓을 분류(classifier)한다", "task_2"))
    result = compose(domain="support", roles=["ClassifierTranslator"], pool=pool)
    decision = result.decisions[0]
    assert decision.action == "reuse_adapted"
    assert decision.source_contract.role == "Classifier"
    assert result.roles_to_generate == []


def test_compose_handles_mixed_roles_independently(pool: PoolIndex) -> None:
    pool.add(_contract("Classifier", "support", "티켓을 분류한다", "task_1"))
    result = compose(domain="support", roles=["Classifier", "Translator"], pool=pool)
    actions = {d.role: d.action for d in result.decisions}
    assert actions["Classifier"] == "reuse_exact"
    assert actions["Translator"] == "flag_for_human"  # support 도메인 후보는 있지만 안 맞음
    assert result.roles_to_generate == ["Translator"]
