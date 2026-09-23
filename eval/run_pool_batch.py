#!/usr/bin/env python3
"""Part X(F5-F8) 실측 하네스 — 3개 브리프를 같은 pool 인스턴스로 순차 실행해,
2·3번째 브리프가 실제로 첫 브리프의 역할을 재사용/부족분만 생성하는지 잰다.

골든셋 배치(run_batch.py, v2_cases.json)의 8개 브리프는 전부 도메인이 달라(Ch
매핑표 참고) pool 재사용이 애초에 걸릴 기회가 없다 — 그래서 Gate F가 별도
하네스(run_multiagent.py)를 쓰는 것과 같은 이유로, 여기도 도메인이 겹치도록
설계한 별도 골든셋(v4_pool_cases.json)과 별도 하네스를 쓴다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentforge.eval_wiring import monitor, pool, run  # noqa: E402


def main() -> int:
    golden_path = Path(__file__).resolve().parents[1] / "data" / "golden_examples" / "v4_pool_cases.json"
    cases = json.loads(golden_path.read_text(encoding="utf-8"))

    for case in cases:
        try:
            run(case["brief"])
            print(f"✅ {case['id']}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ {case['id']}: {exc}")

    path = monitor.save_to_file("gate_run_pool")
    print(f"\n저장됨: {path}")

    print("\n최종 Pool 상태:")
    for contract in pool.all():
        print(f"  - {contract.role} (domain={contract.domain}, source={contract.source_task_id})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
