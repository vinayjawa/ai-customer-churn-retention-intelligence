"""Customer-level SHAP explanations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from churn_intel.explain.shap_utils import (
    EXPLANATION_SCALE,
    build_linear_explainer,
    feature_names,
    shap_values_matrix,
    transformed_matrix,
    validate_alignment,
)
from churn_intel.modeling.artifacts import load_pipeline
from churn_intel.modeling.train import DECISION_THRESHOLD


@dataclass
class CustomerExplanation:
    churn_probability: float
    predicted_churn: int
    decision_threshold: float
    explanation_scale: str
    top_positive_contributors: list[dict[str, float]]
    top_negative_contributors: list[dict[str, float]]
    interpretation: str


def explain_customer_record(
    record: pd.Series | dict,
    *,
    pipeline=None,
    background_X: pd.DataFrame | None = None,
    top_k: int = 5,
) -> CustomerExplanation:
    """
    Explain one customer feature row (no customerID required in record).
    SHAP values are in log-odds units; probability comes from predict_proba.
    Positive SHAP -> pushes log-odds toward churn (class 1).
    """
    pipe = pipeline or load_pipeline()
    if isinstance(record, dict):
        row = pd.DataFrame([record])
    else:
        row = pd.DataFrame([record.drop(labels=[c for c in record.index if c in {"customerID", "Churn", "ChurnLabel"}], errors="ignore")])

    if "customerID" in row.columns:
        row = row.drop(columns=["customerID"])
    for col in ("Churn", "ChurnLabel", "ingest_batch_id", "loaded_at_utc"):
        if col in row.columns:
            row = row.drop(columns=[col])

    proba = float(pipe.predict_proba(row)[0, 1])
    pred = int(proba >= DECISION_THRESHOLD)

    if background_X is None:
        raise ValueError("background_X is required to compute SHAP for a single record.")

    explainer = build_linear_explainer(pipe, background_X)
    names = feature_names(pipe)
    row_t = transformed_matrix(pipe, row)
    values = shap_values_matrix(explainer, row_t)[0]
    validate_alignment(values.reshape(1, -1), names)

    pairs = list(zip(names, values, strict=False))
    pairs_sorted = sorted(pairs, key=lambda x: x[1], reverse=True)
    top_pos = [{"feature": f, "shap_log_odds": float(v)} for f, v in pairs_sorted[:top_k]]
    top_neg = [{"feature": f, "shap_log_odds": float(v)} for f, v in pairs_sorted[-top_k:]][::-1]

    interpretation = (
        "Contributions are SHAP values in log-odds space for the churn class. "
        "Positive values increase predicted churn risk relative to the explainer baseline; "
        "negative values decrease it. This does not imply that changing a feature will cause churn to change."
    )

    return CustomerExplanation(
        churn_probability=proba,
        predicted_churn=pred,
        decision_threshold=DECISION_THRESHOLD,
        explanation_scale=EXPLANATION_SCALE,
        top_positive_contributors=top_pos,
        top_negative_contributors=top_neg,
        interpretation=interpretation,
    )
