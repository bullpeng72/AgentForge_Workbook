"""`agentforge-webui` 진입점 — Web UI만 필요할 땐 PerformanceMonitor/LLM 클라이언트
전체를 끌어오는 eval_wiring을 거치지 않는다(원칙 — 최소 의존). Pool(SQLite)과
results/·.aoo/ 디렉터리만 직접 연다."""
from __future__ import annotations

import argparse

import uvicorn

from agentforge.pool.index import PoolIndex
from agentforge.webui.app import create_app


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentForge Web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--pool-db", default="results/pool_index.db")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--aoo-dir", default=".aoo")
    args = parser.parse_args()

    pool = PoolIndex(db_path=args.pool_db)
    app = create_app(pool, results_dir=args.results_dir, aoo_dir=args.aoo_dir)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
