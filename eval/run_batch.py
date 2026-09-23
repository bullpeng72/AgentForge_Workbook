#!/usr/bin/env python3
"""8개 골든 케이스를 전부 실제 GPT-5+Ollama로 계측 실행하고 results/에 저장한다.

Part VII(Gate 정면돌파) 첫 실측 — Archivist 책의 eval/run_batch.py와 같은 역할.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentforge.eval_wiring import monitor, run  # noqa: E402


def main() -> int:
    golden_path = Path(__file__).resolve().parents[1] / "data" / "golden_examples" / "v2_cases.json"
    cases = json.loads(golden_path.read_text(encoding="utf-8"))

    for case in cases:
        try:
            run(case["brief"])
            print(f"✅ {case['id']}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ {case['id']}: {exc}")

    path = monitor.save_to_file("gate_run_1")
    print(f"\n저장됨: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
