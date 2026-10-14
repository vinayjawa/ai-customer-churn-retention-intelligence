"""Persist churn scores to ml schema."""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from churn_intel.config import PROJECT_ROOT
from churn_intel.db import create_db_engine, execute_sql_file
from churn_intel.modeling.artifacts import MODEL_NAME, MODEL_VERSION

logger = logging.getLogger(__name__)

DDL_PATH = PROJECT_ROOT / "sql" / "ddl" / "07_ml_scoring_columns.sql"


def apply_scoring_ddl() -> None:
    if DDL_PATH.is_file():
        engine = create_db_engine()
        try:
            execute_sql_file(engine, DDL_PATH)
        finally:
            engine.dispose()


def _ensure_model_registry(conn) -> int:
    existing = conn.execute(
        text(
            """
            SELECT TOP 1 model_id
            FROM ml.model_registry
            WHERE model_name = :name AND model_version = :version
            ORDER BY model_id DESC
            """
        ),
        {"name": MODEL_NAME, "version": MODEL_VERSION},
    ).scalar()
    if existing is not None:
        return int(existing)

    result = conn.execute(
        text(
            """
            INSERT INTO ml.model_registry (model_name, model_version, artifact_path, notes)
            OUTPUT INSERTED.model_id
            VALUES (:name, :version, :path, :notes)
            """
        ),
        {
            "name": MODEL_NAME,
            "version": MODEL_VERSION,
            "path": "artifacts/models/baseline_churn_pipeline.joblib",
            "notes": "Phase 5 batch scoring — logistic regression baseline",
        },
    )
    return int(result.scalar_one())


def persist_scores_to_sql(scores: pd.DataFrame) -> int:
    """
    Append score history rows (one row per customer per scoring run).
    Does not delete prior score records.
    """
    engine = create_db_engine()
    insert_sql = text(
        """
        INSERT INTO ml.customer_churn_score (
            customerID, model_id, churn_probability, predicted_churn, model_version, scored_at_utc
        )
        VALUES (:customerID, :model_id, :churn_probability, :predicted_churn, :model_version, :scored_at_utc)
        """
    )

    inserted = 0
    with engine.begin() as conn:
        model_id = _ensure_model_registry(conn)
        for row in scores.itertuples(index=False):
            scored_at = row.scored_at_utc
            if isinstance(scored_at, str):
                scored_at = datetime.fromisoformat(scored_at.replace("Z", "+00:00")).replace(tzinfo=None)
            conn.execute(
                insert_sql,
                {
                    "customerID": row.customerID,
                    "model_id": model_id,
                    "churn_probability": float(row.churn_probability),
                    "predicted_churn": int(row.predicted_churn),
                    "model_version": row.model_version,
                    "scored_at_utc": scored_at,
                },
            )
            inserted += 1
    engine.dispose()
    logger.info("Inserted %s score rows into ml.customer_churn_score", inserted)
    return inserted
