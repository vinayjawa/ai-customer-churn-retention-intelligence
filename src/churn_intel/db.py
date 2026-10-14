"""SQLAlchemy engine helpers and SQL script execution."""

from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from churn_intel.config import get_settings

_GO_BATCH = re.compile(r"^\s*GO\s*$", re.IGNORECASE)


def create_db_engine(*, echo: bool = False) -> Engine:
    settings = get_settings()
    url = settings.build_database_url()
    return create_engine(url, echo=echo, future=True)


def split_sql_batches(script: str) -> list[str]:
    """Split a T-SQL script on standalone GO lines (SSMS style)."""
    batches: list[str] = []
    current: list[str] = []
    for line in script.splitlines():
        if _GO_BATCH.match(line):
            batch = "\n".join(current).strip()
            if batch:
                batches.append(batch)
            current = []
        else:
            current.append(line)
    tail = "\n".join(current).strip()
    if tail:
        batches.append(tail)
    return batches


def execute_sql_file(engine: Engine, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    batches = split_sql_batches(sql)
    with engine.begin() as conn:
        for batch in batches:
            conn.exec_driver_sql(batch)


def execute_sql_files(engine: Engine, paths: list[Path]) -> None:
    for path in paths:
        execute_sql_file(engine, path)
