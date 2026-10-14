"""Churn rate and summary metrics."""

from __future__ import annotations

import pandas as pd


def compute_churn_rate(churn_series: pd.Series) -> float:
    """
    Compute churn rate from a binary churn indicator (1=churned, 0=retained).
    Returns NaN when there are zero rows.
    """
    if len(churn_series) == 0:
        return float("nan")
    return float(churn_series.astype(int).sum()) / float(len(churn_series))


def segment_summary(df: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    """Customer count, churn count, and churn rate by segment column."""
    grouped = (
        df.groupby(segment_col, dropna=False)
        .agg(
            customer_count=("Churn", "size"),
            churn_count=("Churn", "sum"),
        )
        .reset_index()
    )
    grouped["churn_rate"] = grouped["churn_count"] / grouped["customer_count"].replace(0, pd.NA)
    return grouped.sort_values(["churn_rate", "customer_count"], ascending=[False, False])
