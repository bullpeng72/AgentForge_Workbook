from __future__ import annotations

import sqlite3
from pathlib import Path

from agentforge.pool.contract import AgentContract

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS pool_agents (
    source_task_id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    domain TEXT NOT NULL,
    contract_json TEXT NOT NULL
)
"""


class PoolIndex:
    """ADR_T-D8D8CE.md 결정 4 — results/*.json이 원천, 이건 검색용 SQLite 인덱스일
    뿐이다(agent_evaluator.storage.sqlite_backend와 같은 설계: 최소 스칼라 컬럼 +
    전체 상태를 담은 json 블롭, 스키마 마이그레이션 부담 최소화). 별도 Pool 전용
    DB 스키마를 새로 설계하지 않는다(원칙4) — 같은 패턴만 가져온다."""

    def __init__(self, db_path: str | Path = "results/pool_index.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    def add(self, contract: AgentContract) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO pool_agents (source_task_id, role, domain, contract_json) "
            "VALUES (?, ?, ?, ?)",
            (contract.source_task_id, contract.role, contract.domain, contract.model_dump_json()),
        )
        self._conn.commit()

    def search_by_domain(self, domain: str) -> list[AgentContract]:
        rows = self._conn.execute(
            "SELECT contract_json FROM pool_agents WHERE domain = ?", (domain,)
        ).fetchall()
        return [AgentContract.model_validate_json(row[0]) for row in rows]

    def all(self) -> list[AgentContract]:
        rows = self._conn.execute("SELECT contract_json FROM pool_agents").fetchall()
        return [AgentContract.model_validate_json(row[0]) for row in rows]

    def close(self) -> None:
        self._conn.close()
