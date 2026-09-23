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
    DB 스키마를 새로 설계하지 않는다(원칙4) — 같은 패턴만 가져온다.

    실측(Part XI, Web UI를 FastAPI 스레드풀 아래서 돌려보고 발견): 이전엔
    `__init__`에서 커넥션을 한 번 열어 인스턴스 수명 내내 재사용했다 — CLI/eval
    스크립트(항상 단일 스레드)에선 문제가 없었지만, FastAPI 동기 라우트는 요청마다
    다른 워커 스레드에서 실행돼 `sqlite3.ProgrammingError: SQLite objects created
    in a thread can only be used in that same thread`가 났다. `sqlite_backend.py`가
    실제로 하는 것(재사용할 "같은 패턴"의 진짜 모습)은 호출마다 커넥션을 새로
    열고 닫는 것이었다 — 그걸 그대로 따라간다."""

    def __init__(self, db_path: str | Path = "results/pool_index.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.execute(_CREATE_TABLE)
        conn.commit()
        conn.close()

    def add(self, contract: AgentContract) -> None:
        conn = sqlite3.connect(str(self._db_path))
        try:
            conn.execute(
                "INSERT OR REPLACE INTO pool_agents (source_task_id, role, domain, contract_json) "
                "VALUES (?, ?, ?, ?)",
                (contract.source_task_id, contract.role, contract.domain, contract.model_dump_json()),
            )
            conn.commit()
        finally:
            conn.close()

    def search_by_domain(self, domain: str) -> list[AgentContract]:
        conn = sqlite3.connect(str(self._db_path))
        try:
            rows = conn.execute(
                "SELECT contract_json FROM pool_agents WHERE domain = ?", (domain,)
            ).fetchall()
        finally:
            conn.close()
        return [AgentContract.model_validate_json(row[0]) for row in rows]

    def all(self) -> list[AgentContract]:
        conn = sqlite3.connect(str(self._db_path))
        try:
            rows = conn.execute("SELECT contract_json FROM pool_agents").fetchall()
        finally:
            conn.close()
        return [AgentContract.model_validate_json(row[0]) for row in rows]
