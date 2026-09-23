from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def find_run_harness_groups_for_task(
    origin_task_id: str, results_dir: str | Path = "results"
) -> tuple[str, dict[str, Any]] | None:
    """ADR 결정 6 — Pool 항목의 origin_task_id로 results/*.json을 역참조한다.

    주의: `harness_groups`는 태스크 하나가 아니라 **그 태스크가 포함된 실행(run)
    전체**의 Gate A-G 집계 점수다(SDK가 태스크별 Gate 점수를 따로 안 남긴다) —
    그래서 "이 에이전트 자체의 점수"가 아니라 "이 에이전트를 만들어낸 실행이
    전체적으로 받은 점수"로 읽어야 한다. Web UI는 이 사실을 그대로 보여준다
    (파일명 + 실행 전체 점수), 없는 걸 있는 척 만들어내지 않는다.

    origin_task_id를 가진 태스크가 없거나, 파일이 깨졌거나, results_dir이
    없으면 조용히 None을 반환한다(Web UI가 죽으면 안 된다). 찾으면
    (파일명, harness_groups)를 반환한다."""
    root = Path(results_dir)
    if not root.is_dir():
        return None

    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue

        tasks = data.get("tasks", data.get("task_results", []))
        if not isinstance(tasks, list):
            continue

        for task in tasks:
            if not isinstance(task, dict):
                continue
            if task.get("task_id") == origin_task_id:
                extra_metrics = data.get("extra_metrics", {})
                if isinstance(extra_metrics, dict):
                    groups = extra_metrics.get("harness_groups")
                    if isinstance(groups, dict):
                        return path.name, groups
                return None

    return None
