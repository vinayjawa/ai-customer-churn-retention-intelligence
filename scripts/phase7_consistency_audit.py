"""Read-only Phase 7 consistency checks (no writes)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from churn_intel.analytics.load import load_customer_mart
from churn_intel.config import PROJECT_ROOT
from churn_intel.dashboard.data import load_scores_from_sql, select_latest_score_batch
from churn_intel.dashboard.metrics import compute_overview_kpis
from churn_intel.db import create_db_engine
from churn_intel.modeling.artifacts import load_metadata, load_pipeline

ROOT = PROJECT_ROOT


def main() -> None:
    results: dict[str, object] = {}

    df = load_customer_mart()
    churn = df["Churn"].astype(int)
    results["customers"] = {
        "rows": len(df),
        "distinct_ids": int(df["customerID"].nunique()),
        "churn_yes": int((churn == 1).sum()),
        "churn_no": int((churn == 0).sum()),
        "churn_rate": float(churn.mean()),
    }

    meta = load_metadata()
    results["model_metadata"] = {
        "selected_model": meta.get("selected_model"),
        "feature_count_after_encoding": meta.get("feature_count_after_encoding"),
        "decision_threshold": meta.get("decision_threshold"),
    }

    metrics = pd.read_csv(ROOT / "artifacts/evaluation/baseline_metrics_comparison.csv")
    results["baseline_metrics"] = metrics.to_dict(orient="records")

    shap = pd.read_csv(ROOT / "artifacts/explainability/global_feature_importance.csv")
    results["shap_feature_rows"] = len(shap)

    pipe = load_pipeline()
    encoded = len(pipe.named_steps["preprocessor"].get_feature_names_out())
    results["pipeline_encoded_features"] = encoded

    scores, score_meta = load_scores_from_sql()
    merged = df.merge(scores[["customerID", "churn_probability", "predicted_churn"]], on="customerID")
    kpis = compute_overview_kpis(df, scores)
    results["scores"] = {
        "meta": score_meta.__dict__,
        "high_risk_threshold": kpis.get("high_risk_threshold"),
        "high_risk_count": kpis.get("high_risk_count"),
        "predicted_churn_at_0_5": kpis.get("predicted_churn_at_0_5"),
    }

    engine = create_db_engine()
    with engine.connect() as conn:
        batches = conn.execute(
            text(
                "SELECT scored_at_utc, model_version, COUNT(*) cnt "
                "FROM ml.customer_churn_score GROUP BY scored_at_utc, model_version ORDER BY scored_at_utc"
            )
        ).fetchall()
    engine.dispose()
    results["score_batches"] = [tuple(map(str, b)) for b in batches]

    out = ROOT / "artifacts" / "evaluation" / "phase7_consistency_audit.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
