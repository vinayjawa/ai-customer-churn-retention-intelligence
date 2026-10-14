from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

from churn_intel.explain.local import explain_customer_record
from churn_intel.explain.shap_utils import validate_alignment
from churn_intel.modeling.data import prepare_modeling_frame
from churn_intel.retention.rules import recommend_for_profile
from churn_intel.scoring.batch import score_customers
from tests.unit.test_modeling import _synthetic_frame


def _tiny_pipeline() -> Pipeline:
    df = _synthetic_frame(120)
    X, y, _ = prepare_modeling_frame(df)
    pre = ColumnTransformer(
        [
            ("num", SimpleImputer(strategy="median"), ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen", "total_charges_blank"]),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                [c for c in X.columns if c not in {"tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen", "total_charges_blank"}],
            ),
        ]
    )
    pipe = Pipeline([("preprocessor", pre), ("classifier", LogisticRegression(max_iter=500))])
    pipe.fit(X, y)
    return pipe, X


def test_probability_range_and_threshold(monkeypatch, tmp_path) -> None:
    pipe, X = _tiny_pipeline()
    df = _synthetic_frame(80)
    monkeypatch.setattr("churn_intel.scoring.batch.load_pipeline", lambda: pipe)
    monkeypatch.setattr("churn_intel.scoring.batch.load_metadata", lambda: {"selected_model": "test"})
    monkeypatch.setattr("churn_intel.scoring.batch.PROCESSED_DIR", tmp_path)
    scores, meta = score_customers(df=df, write_sql=False)
    assert meta["rows_scored"] == 80
    assert scores["churn_probability"].between(0, 1).all()
    assert set(scores["predicted_churn"].unique()).issubset({0, 1})


def test_customer_explanation_dimensions() -> None:
    pipe, X = _tiny_pipeline()
    record = X.iloc[0]
    exp = explain_customer_record(record, pipeline=pipe, background_X=X)
    assert 0.0 <= exp.churn_probability <= 1.0
    assert exp.predicted_churn in (0, 1)
    assert len(exp.top_positive_contributors) > 0
    assert exp.explanation_scale == "log-odds"


def test_shap_alignment_helper() -> None:
    values = np.zeros((5, 10))
    names = np.array([f"f{i}" for i in range(10)])
    validate_alignment(values, names)
    with pytest.raises(ValueError):
        validate_alignment(values, names[:8])


def test_recommendation_rules_only_for_high_risk() -> None:
    low = recommend_for_profile(
        contract="Month-to-month",
        tenure=3,
        payment_method="Electronic check",
        online_security="No",
        tech_support="No",
        high_risk=False,
    )
    high = recommend_for_profile(
        contract="Month-to-month",
        tenure=3,
        payment_method="Electronic check",
        online_security="No",
        tech_support="No",
        high_risk=True,
    )
    assert low == []
    assert len(high) >= 1


def test_scores_exclude_customerid_from_model_features(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    def fake_proba(X):
        captured["columns"] = list(X.columns)
        n = len(X)
        return np.column_stack([np.zeros(n), np.ones(n) * 0.4])

    pipe, _ = _tiny_pipeline()
    pipe.predict_proba = fake_proba  # type: ignore[method-assign]
    df = _synthetic_frame(30)
    monkeypatch.setattr("churn_intel.scoring.batch.load_pipeline", lambda: pipe)
    monkeypatch.setattr("churn_intel.scoring.batch.load_metadata", lambda: {})
    monkeypatch.setattr("churn_intel.scoring.batch.PROCESSED_DIR", tmp_path)
    score_customers(df=df, write_sql=False)
    assert "customerID" not in captured["columns"]
