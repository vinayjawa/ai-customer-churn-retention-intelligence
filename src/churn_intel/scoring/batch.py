"""Score customers from analytics.customer."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from churn_intel.analytics.load import load_customer_mart
from churn_intel.config import PROJECT_ROOT
from churn_intel.modeling.artifacts import MODEL_VERSION, load_metadata, load_pipeline
from churn_intel.modeling.data import prepare_modeling_frame
from churn_intel.modeling.train import DECISION_THRESHOLD
from churn_intel.scoring.sql_store import apply_scoring_ddl, persist_scores_to_sql

logger = logging.getLogger(__name__)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "retention"


def score_customers(
    *,
    df: pd.DataFrame | None = None,
    sample_size: int | None = None,
    write_sql: bool = True,
) -> tuple[pd.DataFrame, dict[str, object]]:
    pipeline = load_pipeline()
    metadata = load_metadata()

    raw = df if df is not None else load_customer_mart()
    if sample_size is not None:
        raw = raw.sample(n=min(sample_size, len(raw)), random_state=42)

    customer_ids = raw["customerID"].astype(str)
    X, _, validation_meta = prepare_modeling_frame(raw)

    proba = pipeline.predict_proba(X)[:, 1]
    if (proba < 0).any() or (proba > 1).any():
        raise ValueError("Predicted probabilities outside [0, 1].")

    scored_at = datetime.now(timezone.utc).replace(microsecond=0)
    scores = pd.DataFrame(
        {
            "customerID": customer_ids.values,
            "churn_probability": proba,
            "predicted_churn": (proba >= DECISION_THRESHOLD).astype(int),
            "model_version": MODEL_VERSION,
            "scored_at_utc": scored_at.isoformat(),
            "artifact": "baseline_churn_pipeline.joblib",
        }
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "customer_churn_scores.csv"
    scores.to_csv(out_path, index=False)

    write_meta: dict[str, object] = {
        "rows_scored": len(scores),
        "output_csv": str(out_path),
        "validation_meta": validation_meta,
        "decision_threshold": DECISION_THRESHOLD,
        "model_version": MODEL_VERSION,
        "sql_rows_written": 0,
    }

    if write_sql:
        apply_scoring_ddl()
        rows = persist_scores_to_sql(scores)
        write_meta["sql_rows_written"] = rows

    logger.info("Scored %s customers", len(scores))
    return scores, write_meta
