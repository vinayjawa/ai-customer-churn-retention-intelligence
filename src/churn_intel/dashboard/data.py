"""Read-only dashboard data loaders (SQL + local artifacts)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from churn_intel.analytics.bands import add_band_columns
from churn_intel.analytics.load import load_customer_mart
from churn_intel.config import PROJECT_ROOT
from churn_intel.dashboard.constants import REFERENCE_CUSTOMER_COUNT
from churn_intel.db import create_db_engine

logger = logging.getLogger(__name__)

SCORES_CSV = PROJECT_ROOT / "data" / "processed" / "retention" / "customer_churn_scores.csv"
METRICS_CSV = PROJECT_ROOT / "artifacts" / "evaluation" / "baseline_metrics_comparison.csv"
SHAP_CSV = PROJECT_ROOT / "artifacts" / "explainability" / "global_feature_importance.csv"
SHAP_SUMMARY_PNG = PROJECT_ROOT / "artifacts" / "explainability" / "shap_summary_plot.png"
SHAP_BAR_PNG = PROJECT_ROOT / "artifacts" / "explainability" / "shap_bar_plot.png"
RETENTION_SEG_CSV = PROJECT_ROOT / "data" / "processed" / "retention" / "retention_segment_summary.csv"
RETENTION_REC_CSV = PROJECT_ROOT / "data" / "processed" / "retention" / "retention_recommendation_summary.csv"
HIGH_RISK_CSV = PROJECT_ROOT / "data" / "processed" / "retention" / "high_risk_customers_anonymized_top100.csv"
RETENTION_META = PROJECT_ROOT / "data" / "processed" / "retention" / "retention_analysis_metadata.txt"

FORBIDDEN_DISPLAY_COLUMNS = {"customerID", "ingest_batch_id", "loaded_at_utc"}


@dataclass
class ScoreSnapshotMeta:
    source: str
    scored_at_utc: str | None
    model_version: str | None
    row_count: int
    distinct_customers: int
    warning: str | None = None


def select_latest_score_batch(score_history: pd.DataFrame) -> tuple[pd.DataFrame, ScoreSnapshotMeta]:
    """
    Latest snapshot = rows from the most recent scored_at_utc (and model_version within that timestamp).
    Prevents mixing append-only scoring runs.
    """
    if score_history.empty:
        return score_history, ScoreSnapshotMeta("empty", None, None, 0, 0, "No score rows.")

    required = {"customerID", "churn_probability", "scored_at_utc"}
    missing = required - set(score_history.columns)
    if missing:
        raise ValueError(f"Score data missing columns: {missing}")

    work = score_history.copy()
    work["scored_at_utc"] = pd.to_datetime(work["scored_at_utc"], utc=True, errors="coerce")
    latest_ts = work["scored_at_utc"].max()
    latest = work[work["scored_at_utc"] == latest_ts].copy()

    version = None
    if "model_version" in latest.columns and not latest["model_version"].isna().all():
        version = str(latest["model_version"].mode().iloc[0])

    row_count = len(latest)
    distinct = int(latest["customerID"].nunique())
    warning = None
    if distinct != row_count:
        warning = "Duplicate customerID rows in latest scoring batch; deduplicated by keeping last row per customer."
        latest = latest.sort_values("scored_at_utc").drop_duplicates("customerID", keep="last")

    if row_count != REFERENCE_CUSTOMER_COUNT and distinct != REFERENCE_CUSTOMER_COUNT:
        warning = (warning or "") + f" Latest batch size {distinct} differs from reference {REFERENCE_CUSTOMER_COUNT}."

    meta = ScoreSnapshotMeta(
        source="batch_selection",
        scored_at_utc=str(latest_ts) if pd.notna(latest_ts) else None,
        model_version=version,
        row_count=len(latest),
        distinct_customers=int(latest["customerID"].nunique()),
        warning=warning.strip() if warning else None,
    )
    return latest, meta


def load_scores_from_sql() -> tuple[pd.DataFrame, ScoreSnapshotMeta]:
    engine = create_db_engine()
    query = text(
        """
        SELECT customerID, churn_probability, predicted_churn, model_version, scored_at_utc
        FROM ml.customer_churn_score
        """
    )
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        latest, meta = select_latest_score_batch(df)
        meta.source = "sql_server"
        return latest, meta
    finally:
        engine.dispose()


def load_scores_from_csv() -> tuple[pd.DataFrame, ScoreSnapshotMeta]:
    if not SCORES_CSV.is_file():
        empty = pd.DataFrame()
        return empty, ScoreSnapshotMeta("csv", None, None, 0, 0, "Score CSV not found.")
    df = pd.read_csv(SCORES_CSV)
    latest, meta = select_latest_score_batch(df)
    meta.source = "csv_fallback"
    return latest, meta


def load_scores(prefer_sql: bool = True) -> tuple[pd.DataFrame, ScoreSnapshotMeta]:
    if prefer_sql:
        try:
            return load_scores_from_sql()
        except Exception as exc:  # noqa: BLE001 — fallback without secrets
            logger.warning("SQL score load failed; falling back to CSV.")
            csv_df, csv_meta = load_scores_from_csv()
            csv_meta.warning = f"SQL unavailable ({type(exc).__name__}). Using CSV snapshot. {csv_meta.warning or ''}".strip()
            return csv_df, csv_meta
    return load_scores_from_csv()


def load_customers_with_bands() -> pd.DataFrame:
    df = load_customer_mart()
    return add_band_columns(df)


def load_model_metrics() -> pd.DataFrame:
    if not METRICS_CSV.is_file():
        return pd.DataFrame()
    return pd.read_csv(METRICS_CSV)


def load_shap_importance() -> pd.DataFrame:
    if not SHAP_CSV.is_file():
        return pd.DataFrame()
    return pd.read_csv(SHAP_CSV)


def load_retention_tables() -> dict[str, pd.DataFrame | str | None]:
    out: dict[str, pd.DataFrame | str | None] = {
        "segments": pd.read_csv(RETENTION_SEG_CSV) if RETENTION_SEG_CSV.is_file() else pd.DataFrame(),
        "recommendations": pd.read_csv(RETENTION_REC_CSV) if RETENTION_REC_CSV.is_file() else pd.DataFrame(),
        "high_risk_anonymized": pd.read_csv(HIGH_RISK_CSV) if HIGH_RISK_CSV.is_file() else pd.DataFrame(),
        "metadata_text": RETENTION_META.read_text(encoding="utf-8") if RETENTION_META.is_file() else None,
    }
    return out


def sanitize_display_frame(df: pd.DataFrame) -> pd.DataFrame:
    drop = [c for c in df.columns if c in FORBIDDEN_DISPLAY_COLUMNS]
    return df.drop(columns=drop, errors="ignore")
