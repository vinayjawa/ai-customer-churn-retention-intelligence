"""Segment-level retention intelligence (no customer IDs in exported summaries)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from churn_intel.analytics.bands import add_band_columns
from churn_intel.analytics.load import load_customer_mart
from churn_intel.analytics.segments import MIN_SEGMENT_SIZE
from churn_intel.config import PROJECT_ROOT
from churn_intel.modeling.train import DECISION_THRESHOLD
from churn_intel.retention.rules import recommend_for_profile

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "retention"
HIGH_RISK_QUANTILE = 0.75


def run_retention_analysis(scores: pd.DataFrame | None = None) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if scores is None:
        scores_path = OUTPUT_DIR / "customer_churn_scores.csv"
        if not scores_path.is_file():
            raise FileNotFoundError("Run batch scoring first (customer_churn_scores.csv missing).")
        scores = pd.read_csv(scores_path)

    customers = load_customer_mart()
    merged = customers.merge(scores[["customerID", "churn_probability", "predicted_churn"]], on="customerID")
    merged = add_band_columns(merged)

    risk_threshold = float(merged["churn_probability"].quantile(HIGH_RISK_QUANTILE))
    merged["high_risk"] = merged["churn_probability"] >= risk_threshold

    # Anonymized high-risk rank file (no customerID)
    high = merged.sort_values("churn_probability", ascending=False).head(100).reset_index(drop=True)
    high["anonymized_rank"] = high.index + 1
    high_export = high[
        [
            "anonymized_rank",
            "churn_probability",
            "predicted_churn",
            "Contract",
            "tenure_band",
            "PaymentMethod",
            "InternetService",
            "OnlineSecurity",
            "TechSupport",
            "Churn",
        ]
    ].rename(columns={"Churn": "actual_churn_observed"})
    high_path = OUTPUT_DIR / "high_risk_customers_anonymized_top100.csv"
    high_export.to_csv(high_path, index=False)

    def segment_table(col: str, label: str) -> pd.DataFrame:
        g = (
            merged.groupby(col, dropna=False)
            .agg(
                customer_count=("customerID", "size"),
                avg_predicted_risk=("churn_probability", "mean"),
                high_risk_count=("high_risk", "sum"),
                actual_churn_rate=("Churn", "mean"),
            )
            .reset_index()
        )
        g.insert(0, "segment_type", label)
        g = g.rename(columns={col: "segment_value"})
        return g[g["customer_count"] >= MIN_SEGMENT_SIZE]

    segments = pd.concat(
        [
            segment_table("Contract", "Contract"),
            segment_table("tenure_band", "TenureBand"),
            segment_table("PaymentMethod", "PaymentMethod"),
            segment_table("OnlineSecurity", "OnlineSecurity"),
            segment_table("TechSupport", "TechSupport"),
        ],
        ignore_index=True,
    )
    segments = segments.sort_values(
        ["high_risk_count", "avg_predicted_risk"], ascending=[False, False]
    )
    seg_path = OUTPUT_DIR / "retention_segment_summary.csv"
    segments.to_csv(seg_path, index=False)

    # Rule mapping counts (aggregated)
    rec_rows: list[dict[str, object]] = []
    high_risk = merged[merged["high_risk"]]
    for _, row in high_risk.iterrows():
        for rec in recommend_for_profile(
            contract=str(row["Contract"]),
            tenure=int(row["tenure"]),
            payment_method=str(row["PaymentMethod"]),
            online_security=str(row["OnlineSecurity"]),
            tech_support=str(row["TechSupport"]),
            high_risk=True,
        ):
            rec_rows.append({"recommendation_code": rec.code, "recommendation_text": rec.text})
    rec_df = (
        pd.DataFrame(rec_rows)
        .value_counts(["recommendation_code", "recommendation_text"])
        .reset_index(name="eligible_high_risk_customers")
        .sort_values("eligible_high_risk_customers", ascending=False)
    )
    rec_path = OUTPUT_DIR / "retention_recommendation_summary.csv"
    rec_df.to_csv(rec_path, index=False)

    meta_path = OUTPUT_DIR / "retention_analysis_metadata.txt"
    meta_path.write_text(
        "\n".join(
            [
                f"high_risk_quantile={HIGH_RISK_QUANTILE}",
                f"high_risk_threshold_probability={risk_threshold:.6f}",
                f"decision_threshold_label={DECISION_THRESHOLD}",
                f"total_customers={len(merged)}",
                f"predicted_high_risk_count={int(merged['high_risk'].sum())}",
                "note=Predicted risk is model output; actual_churn_observed is historical label.",
                "roi_estimates=unavailable (no CLV/campaign cost data)",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "high_risk_anonymized": high_path,
        "segment_summary": seg_path,
        "recommendation_summary": rec_path,
        "metadata": meta_path,
    }
