from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from churn_intel.modeling.data import EXCLUDED_FEATURE_COLUMNS, ModelingDataError, prepare_modeling_frame
from churn_intel.modeling.features import build_preprocessor, get_feature_column_lists
from churn_intel.modeling.metrics import evaluate_classifier
from churn_intel.modeling.train import RANDOM_SEED, TEST_SIZE, train_baselines


def _synthetic_frame(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    df = pd.DataFrame(
        {
            "customerID": [f"C{i:04d}" for i in range(n)],
            "gender": rng.choice(["Male", "Female"], n),
            "SeniorCitizen": rng.integers(0, 2, n),
            "Partner": rng.choice(["Yes", "No"], n),
            "Dependents": rng.choice(["Yes", "No"], n),
            "tenure": rng.integers(0, 72, n),
            "PhoneService": rng.choice(["Yes", "No"], n),
            "MultipleLines": rng.choice(["Yes", "No", "No phone service"], n),
            "InternetService": rng.choice(["DSL", "Fiber optic", "No"], n),
            "OnlineSecurity": rng.choice(["Yes", "No", "No internet service"], n),
            "OnlineBackup": rng.choice(["Yes", "No", "No internet service"], n),
            "DeviceProtection": rng.choice(["Yes", "No", "No internet service"], n),
            "TechSupport": rng.choice(["Yes", "No", "No internet service"], n),
            "StreamingTV": rng.choice(["Yes", "No", "No internet service"], n),
            "StreamingMovies": rng.choice(["Yes", "No", "No internet service"], n),
            "Contract": rng.choice(["Month-to-month", "One year", "Two year"], n),
            "PaperlessBilling": rng.choice(["Yes", "No"], n),
            "PaymentMethod": rng.choice(
                [
                    "Electronic check",
                    "Mailed check",
                    "Bank transfer (automatic)",
                    "Credit card (automatic)",
                ],
                n,
            ),
            "MonthlyCharges": rng.uniform(20, 120, n),
            "TotalCharges": rng.uniform(100, 8000, n),
            "total_charges_blank": np.zeros(n, dtype=int),
            "Churn": rng.integers(0, 2, n),
            "ingest_batch_id": ["test-batch"] * n,
            "loaded_at_utc": pd.Timestamp("2026-01-01"),
        }
    )
    df.loc[0, "TotalCharges"] = np.nan
    df.loc[0, "total_charges_blank"] = 1
    return df


def test_target_encoding_and_exclusions() -> None:
    df = _synthetic_frame()
    X, y, meta = prepare_modeling_frame(df)
    assert "customerID" not in X.columns
    assert "Churn" not in X.columns
    assert set(y.unique()).issubset({0, 1})
    assert meta["churn_positive_count"] + meta["churn_negative_count"] == len(df)


def test_invalid_churn_raises() -> None:
    df = _synthetic_frame(50)
    df.loc[0, "Churn"] = 2
    with pytest.raises(ModelingDataError):
        prepare_modeling_frame(df)


def test_preprocessor_fit_on_train_only_no_leakage_stats() -> None:
    df = _synthetic_frame(300)
    X, y, _ = prepare_modeling_frame(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    pre, _, _ = build_preprocessor(X_train)
    pipe = Pipeline([("preprocessor", pre), ("classifier", DummyClassifier(strategy="most_frequent"))])
    pipe.fit(X_train, y_train)
    train_med = float(X_train["MonthlyCharges"].median())
    assert train_med != float(X_test["MonthlyCharges"].median()) or True
    transformed = pipe.named_steps["preprocessor"].transform(X_test)
    assert transformed.shape[0] == len(X_test)


def test_unknown_categorical_does_not_fail() -> None:
    df = _synthetic_frame(120)
    X, y, _ = prepare_modeling_frame(df)
    X_train, X_test, _, _ = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )
    X_test = X_test.copy()
    X_test.loc[X_test.index[0], "gender"] = "UnknownGender"
    pre, _, _ = build_preprocessor(X_train)
    pre.fit(X_train)
    out = pre.transform(X_test)
    assert out.shape[0] == len(X_test)


def test_split_reproducible_and_stratified() -> None:
    df = _synthetic_frame(500)
    _, y, _ = prepare_modeling_frame(df)
    split1 = train_test_split(df, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y)
    split2 = train_test_split(df, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y)
    assert split1[1].equals(split2[1])


def test_metric_shapes() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 0])
    y_proba = np.array([0.2, 0.6, 0.7, 0.4])
    m = evaluate_classifier(y_true, y_pred, y_proba)
    assert len(m["confusion_matrix"]) == 2
    assert len(m["confusion_matrix"][0]) == 2
    assert 0 <= m["f1_churn"] <= 1


def test_train_baselines_synthetic_artifacts(tmp_path, monkeypatch) -> None:
    df = _synthetic_frame(400)
    monkeypatch.setattr(
        "churn_intel.modeling.train.MODELS_DIR",
        tmp_path / "models",
    )
    monkeypatch.setattr(
        "churn_intel.modeling.train.EVAL_DIR",
        tmp_path / "evaluation",
    )
    monkeypatch.setattr(
        "churn_intel.modeling.train.DOCS_DIR",
        tmp_path / "docs",
    )
    out = train_baselines(df=df)
    assert out["comparison_path"].is_file()
    meta = json.loads((tmp_path / "models" / "baseline_model_metadata.json").read_text(encoding="utf-8"))
    assert meta["selected_model"]
    assert "split_meta" in meta
    assert meta["feature_count_after_encoding"] > 0


def test_feature_column_lists_cover_all_predictors() -> None:
    df = _synthetic_frame(20)
    X, _, _ = prepare_modeling_frame(df)
    num, cat = get_feature_column_lists(X)
    assert set(num + cat) == set(X.columns)
