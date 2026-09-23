from __future__ import annotations

import json
from pathlib import Path

from agentforge.pool.gate_lookup import find_run_harness_groups_for_task


def _write_result(path: Path, *, tasks: list[dict], harness_groups: dict) -> None:
    path.write_text(
        json.dumps({"tasks": tasks, "extra_metrics": {"harness_groups": harness_groups}}),
        encoding="utf-8",
    )


def test_finds_harness_groups_for_a_known_task_id(tmp_path: Path) -> None:
    _write_result(
        tmp_path / "gate_run_1.json",
        tasks=[{"task_id": "forge_abc123"}, {"task_id": "forge_def456"}],
        harness_groups={"A": {"score": 0.9, "status": "pass"}},
    )
    found = find_run_harness_groups_for_task("forge_def456", results_dir=tmp_path)
    assert found is not None
    filename, groups = found
    assert filename == "gate_run_1.json"
    assert groups == {"A": {"score": 0.9, "status": "pass"}}


def test_returns_none_for_an_unknown_task_id(tmp_path: Path) -> None:
    _write_result(
        tmp_path / "gate_run_1.json", tasks=[{"task_id": "forge_abc123"}], harness_groups={"A": {"score": 0.9}}
    )
    assert find_run_harness_groups_for_task("forge_nonexistent", results_dir=tmp_path) is None


def test_returns_none_when_results_dir_missing(tmp_path: Path) -> None:
    assert find_run_harness_groups_for_task("forge_abc123", results_dir=tmp_path / "nope") is None


def test_skips_malformed_json_without_raising(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text("{not valid json", encoding="utf-8")
    _write_result(
        tmp_path / "gate_run_1.json", tasks=[{"task_id": "forge_abc123"}], harness_groups={"A": {"score": 0.9}}
    )
    found = find_run_harness_groups_for_task("forge_abc123", results_dir=tmp_path)
    assert found is not None
    assert found[0] == "gate_run_1.json"


def test_skips_non_dict_json_without_raising(tmp_path: Path) -> None:
    (tmp_path / "list_shaped.json").write_text("[1, 2, 3]", encoding="utf-8")
    found = find_run_harness_groups_for_task("forge_abc123", results_dir=tmp_path)
    assert found is None


def test_task_present_but_harness_groups_missing_returns_none(tmp_path: Path) -> None:
    (tmp_path / "gate_run_1.json").write_text(
        json.dumps({"tasks": [{"task_id": "forge_abc123"}], "extra_metrics": {}}), encoding="utf-8"
    )
    assert find_run_harness_groups_for_task("forge_abc123", results_dir=tmp_path) is None
