"""Training data validation and feature/target preparation."""

from __future__ import annotations

import pandas as pd

REFERENCE_ROW_COUNT = 7043
VALID_CHURN_VALUES = {0, 1}

# Target and metadata excluded from predictors (ChurnLabel is derived from Churn).
EXCLUDED_FEATURE_COLUMNS: frozenset[str] = frozenset(
    {
        "customerID",
        "Churn",
        "ChurnLabel",
        "ingest_batch_id",
        "loaded_at_utc",
    }
)


class ModelingDataError(ValueError):
    """Invalid modeling input."""


def validate_modeling_frame(df: pd.DataFrame) -> None:
    if df.empty:
        raise ModelingDataError("Empty dataframe.")

    required = {"customerID", "Churn", "gender", "tenure", "MonthlyCharges", "TotalCharges"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise ModelingDataError(f"Missing required columns: {sorted(missing_cols)}")

    if df["customerID"].isna().any():
        raise ModelingDataError("Null customerID values found.")

    dup = int(df["customerID"].duplicated().sum())
    if dup:
        raise ModelingDataError(f"Duplicate customerID count: {dup}")

    churn_vals = set(df["Churn"].dropna().unique())
    invalid = churn_vals - VALID_CHURN_VALUES
    if invalid:
        raise ModelingDataError(f"Invalid Churn values (expected 0/1): {sorted(invalid)}")

    if len(df) != REFERENCE_ROW_COUNT:
        # Warn via exception only for hard invalids; row mismatch is allowed but surfaced to caller.
        pass


def prepare_modeling_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict[str, object]]:
    """
    Validate and split features/target.
    Target: Churn (1 = churned / Yes, 0 = retained / No).
    """
    validate_modeling_frame(df)

    y = df["Churn"].astype(int)
    cols_to_drop = [c for c in EXCLUDED_FEATURE_COLUMNS if c in df.columns]
    X = df.drop(columns=cols_to_drop)

    leakage = sorted(set(X.columns) & EXCLUDED_FEATURE_COLUMNS)
    if leakage:
        raise ModelingDataError(f"Leakage columns present in features: {leakage}")

    meta = {
        "row_count": len(df),
        "distinct_customer_ids": int(df["customerID"].nunique()),
        "churn_positive_count": int((y == 1).sum()),
        "churn_negative_count": int((y == 0).sum()),
        "null_total_charges": int(df["TotalCharges"].isna().sum()),
        "total_charges_blank_flag": int(df["total_charges_blank"].sum()),
        "reference_row_count": REFERENCE_ROW_COUNT,
        "row_count_matches_reference": len(df) == REFERENCE_ROW_COUNT,
    }
    return X, y, meta
