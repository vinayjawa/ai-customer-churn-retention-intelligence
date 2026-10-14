"""Segment ranking for retention opportunities."""

from __future__ import annotations

import pandas as pd

MIN_SEGMENT_SIZE = 30


def rank_segments(
    summary: pd.DataFrame,
    *,
    min_size: int = MIN_SEGMENT_SIZE,
    segment_type: str,
    segment_value_col: str = "segment_value",
) -> pd.DataFrame:
    """
    Rank segments by churn volume (churn_count), then churn_rate.
    Filters out segments below min_size to reduce noise from tiny groups.
    """
    required = {"customer_count", "churn_count", "churn_rate", segment_value_col}
    missing = required - set(summary.columns)
    if missing:
        raise ValueError(f"Missing columns for ranking: {missing}")

    filtered = summary[summary["customer_count"] >= min_size].copy()
    filtered.insert(0, "segment_type", segment_type)
    return filtered.sort_values(
        ["churn_count", "churn_rate", "customer_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
