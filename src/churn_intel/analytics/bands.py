"""Tenure and monthly charge band definitions (aligned with SQL EDA scripts)."""

from __future__ import annotations

import pandas as pd

TENURE_BAND_LABELS: list[tuple[int, int | None, str]] = [
    (0, 12, "0-12 months"),
    (13, 24, "13-24 months"),
    (25, 48, "25-48 months"),
    (49, None, "49+ months"),
]

CHARGE_BAND_EDGES: list[tuple[float | None, float | None, str]] = [
    (None, 35, "Under 35"),
    (35, 50, "35-49.99"),
    (50, 70, "50-69.99"),
    (70, 90, "70-89.99"),
    (90, None, "90+"),
]


def assign_tenure_band(tenure: int | float) -> str:
    t = int(tenure)
    for low, high, label in TENURE_BAND_LABELS:
        if high is None and t >= low:
            return label
        if high is not None and low <= t <= high:
            return label
    return "Unmapped"


def assign_monthly_charge_band(charge: float) -> str:
    if charge < 35:
        return "Under 35"
    if charge < 50:
        return "35-49.99"
    if charge < 70:
        return "50-69.99"
    if charge < 90:
        return "70-89.99"
    return "90+"


def add_band_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["tenure_band"] = out["tenure"].map(assign_tenure_band)
    out["monthly_charge_band"] = out["MonthlyCharges"].astype(float).map(assign_monthly_charge_band)
    return out
