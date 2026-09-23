from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agentforge.pool.contract import AgentContract
from agentforge.pool.index import PoolIndex
from agentforge.webui.app import create_app


@pytest.fixture
def pool(tmp_path: Path) -> PoolIndex:
    return PoolIndex(db_path=tmp_path / "pool.db")


def _contract(role: str, domain: str, task_id: str, origin_task_id: str | None = None) -> AgentContract:
    return AgentContract(
        role=role,
        domain=domain,
        input_description=f"{domain} 입력",
        output_description=f"{role} 출력",
        source_task_id=task_id,
        agents_yaml_snippet=f"agents:\n  - name: {role}\n    role: {role}\n",
        origin_task_id=origin_task_id,
    )


def _client(pool: PoolIndex, tmp_path: Path) -> TestClient:
    results_dir = tmp_path / "results"
    aoo_dir = tmp_path / ".aoo"
    results_dir.mkdir(exist_ok=True)
    aoo_dir.mkdir(exist_ok=True)
    app = create_app(pool, results_dir=results_dir, aoo_dir=aoo_dir)
    return TestClient(app)


def test_home_lists_all_four_screens(pool: PoolIndex, tmp_path: Path) -> None:
    r = _client(pool, tmp_path).get("/")
    assert r.status_code == 200
    for href in ("/pool", "/compose", "/evaluate", "/approvals"):
        assert href in r.text


def test_pool_browser_empty_shows_empty_state(pool: PoolIndex, tmp_path: Path) -> None:
    r = _client(pool, tmp_path).get("/pool")
    assert r.status_code == 200
    assert "조건에 맞는 pool 항목이 없습니다" in r.text


def test_pool_browser_filters_by_role_and_domain(pool: PoolIndex, tmp_path: Path) -> None:
    pool.add(_contract("Classifier", "support", "task_1"))
    pool.add(_contract("Translator", "support", "task_2"))
    pool.add(_contract("Classifier", "legal", "task_3"))
    client = _client(pool, tmp_path)

    r = client.get("/pool", params={"role": "Classifier"})
    assert "task_1" in r.text and "task_3" in r.text and "task_2" not in r.text

    r = client.get("/pool", params={"domain": "support"})
    assert "task_1" in r.text and "task_2" in r.text and "task_3" not in r.text


def test_pool_browser_shows_unmeasured_when_no_origin_task_id(pool: PoolIndex, tmp_path: Path) -> None:
    pool.add(_contract("Classifier", "support", "task_1", origin_task_id=None))
    r = _client(pool, tmp_path).get("/pool")
    assert "미측정" in r.text


def test_pool_browser_resolves_gate_scores_via_origin_task_id(pool: PoolIndex, tmp_path: Path) -> None:
    pool.add(_contract("Classifier", "support", "task_1", origin_task_id="forge_abc"))
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "gate_run_1.json").write_text(
        json.dumps(
            {
                "tasks": [{"task_id": "forge_abc"}],
                "extra_metrics": {"harness_groups": {"A": {"score": 0.9, "status": "pass"}, "overall": {"score": 0.9, "status": "pass"}}},
            }
        ),
        encoding="utf-8",
    )
    aoo_dir = tmp_path / ".aoo"
    aoo_dir.mkdir(exist_ok=True)
    app = create_app(pool, results_dir=results_dir, aoo_dir=aoo_dir)
    r = TestClient(app).get("/pool")
    assert "gate_run_1.json" in r.text
    assert "0.9" in r.text


def test_compose_screen_without_params_shows_empty_form(pool: PoolIndex, tmp_path: Path) -> None:
    r = _client(pool, tmp_path).get("/compose")
    assert r.status_code == 200
    assert "판단 결과" not in r.text


def test_compose_screen_renders_live_compose_decisions(pool: PoolIndex, tmp_path: Path) -> None:
    pool.add(_contract("Classifier", "support", "task_1"))
    r = _client(pool, tmp_path).get("/compose", params={"domain": "support", "roles": "Classifier"})
    assert "reuse_exact" in r.text
    assert "판단 결과" in r.text


def test_evaluate_list_shows_only_files_with_harness_groups(pool: PoolIndex, tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "with_gates.json").write_text(
        json.dumps({"extra_metrics": {"harness_groups": {"overall": {"score": 0.8, "status": "pass"}}}}),
        encoding="utf-8",
    )
    (results_dir / "without_gates.json").write_text(json.dumps({"extra_metrics": {}}), encoding="utf-8")
    aoo_dir = tmp_path / ".aoo"
    aoo_dir.mkdir(exist_ok=True)
    app = create_app(pool, results_dir=results_dir, aoo_dir=aoo_dir)
    r = TestClient(app).get("/evaluate")
    assert "with_gates.json" in r.text
    assert "without_gates.json" not in r.text


def test_evaluate_detail_renders_full_scorecard(pool: PoolIndex, tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "run.json").write_text(
        json.dumps(
            {
                "extra_metrics": {
                    "harness_groups": {
                        "A": {"score": 0.9, "status": "pass"},
                        "F": {"score": 0.5, "status": "warn"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    aoo_dir = tmp_path / ".aoo"
    aoo_dir.mkdir(exist_ok=True)
    app = create_app(pool, results_dir=results_dir, aoo_dir=aoo_dir)
    r = TestClient(app).get("/evaluate/run.json")
    assert "0.9" in r.text and "0.5" in r.text and "warn" in r.text


def test_evaluate_detail_rejects_path_traversal(pool: PoolIndex, tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    outside = tmp_path / "secret.json"
    outside.write_text(json.dumps({"extra_metrics": {"harness_groups": {"A": {"score": 1.0}}}}), encoding="utf-8")
    aoo_dir = tmp_path / ".aoo"
    aoo_dir.mkdir(exist_ok=True)
    app = create_app(pool, results_dir=results_dir, aoo_dir=aoo_dir)
    r = TestClient(app).get("/evaluate/..%2Fsecret.json")
    assert "1.0" not in r.text


def test_approvals_status_empty_state(pool: PoolIndex, tmp_path: Path) -> None:
    r = _client(pool, tmp_path).get("/approvals")
    assert r.status_code == 200
    assert "과제가 없습니다" in r.text
    assert "승인 이력이 없습니다" in r.text


def test_approvals_status_shows_real_task_and_approval(pool: PoolIndex, tmp_path: Path) -> None:
    aoo_dir = tmp_path / ".aoo"
    (aoo_dir / "tasks").mkdir(parents=True, exist_ok=True)
    (aoo_dir / "tasks" / "T-TEST.json").write_text(
        json.dumps({"task_id": "T-TEST", "title": "테스트 과제", "current_phase": 3}), encoding="utf-8"
    )
    (aoo_dir / "approvals.jsonl").write_text(
        json.dumps({"id": "ap-1", "task_id": "T-TEST", "kind": "spec_review", "status": "pending", "title": "SPEC 검토"})
        + "\n",
        encoding="utf-8",
    )
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    app = create_app(pool, results_dir=results_dir, aoo_dir=aoo_dir)
    r = TestClient(app).get("/approvals")
    assert "T-TEST" in r.text
    assert "spec_review" in r.text
    assert "pending" in r.text
