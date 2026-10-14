"""Execute sql/analytics/eda/*.sql against ChurnIntel and save result CSVs."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from churn_intel.config import PROJECT_ROOT
from churn_intel.db import create_db_engine, split_sql_batches

EDA_SQL_DIR = PROJECT_ROOT / "sql" / "analytics" / "eda"
OUT_DIR = PROJECT_ROOT / "data" / "processed" / "sql_eda"


def _strip_block_comments(script: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", "", script, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", without_blocks).strip()


def _select_statements(script: str) -> list[str]:
    batches = split_sql_batches(_strip_block_comments(script))
    selects: list[str] = []
    for batch in batches:
        if batch.upper().startswith("DECLARE"):
            selects.append(batch)
            continue
        parts = re.split(r";\s*(?=SELECT\s)", batch, flags=re.IGNORECASE)
        for stmt in parts:
            stmt = stmt.strip().rstrip(";")
            if stmt.upper().startswith("SELECT"):
                selects.append(stmt)
    return selects


def run_sql_eda() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_db_engine()
    try:
        for path in sorted(EDA_SQL_DIR.glob("*.sql")):
            script = path.read_text(encoding="utf-8")
            if "DECLARE" in script.upper() and "WITH segments" in script:
                with engine.connect() as conn:
                    df = pd.read_sql(text(script), conn)
                out = OUT_DIR / f"{path.stem}.csv"
                df.to_csv(out, index=False)
                print(f"Wrote {out} ({len(df)} rows)")
                continue

            statements = _select_statements(script)
            for idx, stmt in enumerate(statements, start=1):
                with engine.connect() as conn:
                    df = pd.read_sql(text(stmt), conn)
                suffix = f"_{idx}" if len(statements) > 1 else ""
                out = OUT_DIR / f"{path.stem}{suffix}.csv"
                df.to_csv(out, index=False)
                print(f"Wrote {out} ({len(df)} rows)")
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_sql_eda()
