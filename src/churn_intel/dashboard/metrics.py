"""KPI and segment metric helpers (pure functions for tests)."""

from __future__ import annotations

import pandas as pd

from churn_intel.dashboard.constants import HIGH_RISK_QUANTILE, MODEL_PREDICTION_THRESHOLD


def compute_overview_kpis(customers: pd.DataFrame, scores: pd.DataFrame | None = None) -> dict[str, float | int]:
    if customers.empty:
        return {}

    churn = customers["Churn"].astype(int)
    total = len(customers)
    churned = int((churn == 1).sum())
    retained = int((churn == 0).sum())

    kpis: dict[str, float | int] = {
        "total_customers": total,
        "churned_customers": churned,
        "retained_customers": retained,
        "historical_churn_rate": churned / total if total else 0.0,
        "avg_tenure": float(customers["tenure"].mean()),
        "avg_monthly_charges": float(customers["MonthlyCharges"].mean()),
    }

    if scores is not None and not scores.empty:
        merged = customers.merge(
            scores[["customerID", "churn_probability", "predicted_churn"]],
            on="customerID",
            how="inner",
        )
        threshold = float(merged["churn_probability"].quantile(HIGH_RISK_QUANTILE))
        high_risk = int((merged["churn_probability"] >= threshold).sum())
        kpis.update(
            {
                "scored_customers": len(merged),
                "predicted_churn_at_0_5": int((merged["churn_probability"] >= MODEL_PREDICTION_THRESHOLD).sum()),
                "predicted_retained_at_0_5": int((merged["churn_probability"] < MODEL_PREDICTION_THRESHOLD).sum()),
                "high_risk_count": high_risk,
                "high_risk_rate": high_risk / len(merged) if len(merged) else 0.0,
                "high_risk_threshold": threshold,
            }
        )
    return kpis


def segment_churn_table(customers: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    grouped = (
        customers.groupby(segment_col, dropna=False)
        .agg(customer_count=("Churn", "size"), churn_count=("Churn", "sum"))
        .reset_index()
    )
    grouped["churn_rate"] = grouped["churn_count"] / grouped["customer_count"].replace(0, pd.NA)
    return grouped.sort_values("churn_rate", ascending=False)


def apply_dimension_filters(
    df: pd.DataFrame,
    *,
    contracts: list[str] | None = None,
    payment_methods: list[str] | None = None,
    internet_services: list[str] | None = None,
    tenure_bands: list[str] | None = None,
) -> pd.DataFrame:
    out = df.copy()
    if contracts:
        out = out[out["Contract"].isin(contracts)]
    if payment_methods:
        out = out[out["PaymentMethod"].isin(payment_methods)]
    if internet_services:
        out = out[out["InternetService"].isin(internet_services)]
    if tenure_bands and "tenure_band" in out.columns:
        out = out[out["tenure_band"].isin(tenure_bands)]
    return out
