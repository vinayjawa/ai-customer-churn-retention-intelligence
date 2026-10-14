"""Load validated CSV into SQL Server and refresh analytics layer."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from churn_intel.config import PROJECT_ROOT, get_settings
from churn_intel.db import create_db_engine, execute_sql_file, execute_sql_files, split_sql_batches
from churn_intel.quality.validation import EXPECTED_COLUMNS, ValidationReport, validate_telco_csv

logger = logging.getLogger(__name__)

STG_TABLE = "stg.telco_customer_churn"


@dataclass
class IngestionResult:
    validation: ValidationReport
    ddl_applied: bool
    staging_rows_inserted: int
    analytics_rows: int | None = None
    batch_id: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.validation.passed and not self.errors and self.staging_rows_inserted > 0


def ddl_script_paths() -> list[Path]:
    ddl_dir = PROJECT_ROOT / "sql" / "ddl"
    ordered = [
        "01_schemas.sql",
        "02_stg_telco_customer_churn.sql",
        "03_analytics_customer.sql",
        "04_ml_schema.sql",
        "05_retention_schema.sql",
        "06_analytics_views.sql",
    ]
    return [ddl_dir / name for name in ordered]


def refresh_analytics_from_stg(engine: Engine, batch_id: str) -> None:
    path = PROJECT_ROOT / "sql" / "dml" / "01_refresh_analytics_from_stg.sql"
    sql = path.read_text(encoding="utf-8").replace("__BATCH_ID__", batch_id)

    with engine.begin() as conn:
        for batch in split_sql_batches(sql):
            conn.exec_driver_sql(batch)


def _prepare_staging_frame(df: pd.DataFrame, *, source_file: str, batch_id: str) -> pd.DataFrame:
    out = df.copy()
    out["ingest_batch_id"] = batch_id
    out["ingested_at_utc"] = datetime.now(timezone.utc).replace(tzinfo=None)
    out["source_file"] = source_file
    return out


def load_staging(
    engine: Engine,
    df: pd.DataFrame,
    *,
    source_file: str,
    batch_id: str,
    batch_size: int,
) -> int:
    payload = _prepare_staging_frame(df, source_file=source_file, batch_id=batch_id)
    staging_columns = EXPECTED_COLUMNS + ["ingest_batch_id", "ingested_at_utc", "source_file"]
    payload = payload[staging_columns]

    # SQL Server ODBC limits ~2100 bound parameters per statement (method="multi").
    max_rows_per_insert = max(1, 2000 // len(staging_columns))

    inserted = 0
    with engine.begin() as conn:
        for start in range(0, len(payload), batch_size):
            chunk = payload.iloc[start : start + batch_size]
            chunk.to_sql(
                "telco_customer_churn",
                con=conn,
                schema="stg",
                if_exists="append",
                index=False,
                method="multi",
                chunksize=max_rows_per_insert,
            )
            inserted += len(chunk)
    return inserted


def count_table(engine: Engine, schema: str, table: str) -> int:
    query = text(f"SELECT COUNT(*) AS cnt FROM {schema}.{table}")
    with engine.connect() as conn:
        return int(conn.execute(query).scalar_one())


def run_ingestion(
    csv_path: Path | None = None,
    *,
    apply_ddl: bool = True,
    refresh_analytics: bool = True,
) -> IngestionResult:
    settings = get_settings()
    path = csv_path or settings.csv_path
    validation = validate_telco_csv(path)

    result = IngestionResult(
        validation=validation,
        ddl_applied=False,
        staging_rows_inserted=0,
    )

    for line in validation.summary_lines():
        logger.info(line)

    if not validation.passed:
        result.errors.append("CSV validation failed; aborting database load.")
        return result

    if not settings.is_db_configured():
        result.errors.append(
            "Database not configured. Set CHURN_DB_SERVER in .env (see .env.example)."
        )
        return result

    batch_id = str(uuid.uuid4())
    result.batch_id = batch_id

    try:
        engine = create_db_engine()
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"Failed to create database engine: {exc}")
        return result

    try:
        if apply_ddl:
            execute_sql_files(engine, ddl_script_paths())
            result.ddl_applied = True

        df = pd.read_csv(path, encoding="utf-8")
        source_name = path.name
        inserted = load_staging(
            engine,
            df,
            source_file=source_name,
            batch_id=batch_id,
            batch_size=settings.ingest_batch_size,
        )
        result.staging_rows_inserted = inserted

        if refresh_analytics:
            refresh_analytics_from_stg(engine, batch_id)
            result.analytics_rows = count_table(engine, "analytics", "customer")

        if result.analytics_rows is not None and result.analytics_rows != validation.row_count:
            result.errors.append(
                f"Analytics row count {result.analytics_rows} != CSV row count {validation.row_count}."
            )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Ingestion failed")
        result.errors.append(f"Ingestion failed: {exc}")

    return result
