"""Shared SHAP helpers for the logistic regression pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline

EXPLANATION_SCALE = "log-odds"
"""LinearExplainer SHAP values add to the model log-odds output before the sigmoid."""


def transformed_matrix(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
    pre = pipeline.named_steps["preprocessor"]
    return pre.transform(X)


def feature_names(pipeline: Pipeline) -> np.ndarray:
    pre = pipeline.named_steps["preprocessor"]
    return pre.get_feature_names_out()


def build_linear_explainer(
    pipeline: Pipeline,
    background_X: pd.DataFrame,
    *,
    max_background: int = 500,
) -> shap.LinearExplainer:
    pre = pipeline.named_steps["preprocessor"]
    clf = pipeline.named_steps["classifier"]
    bg = background_X
    if len(bg) > max_background:
        bg = bg.sample(n=max_background, random_state=42)
    bg_t = pre.transform(bg)
    names = pre.get_feature_names_out()
    return shap.LinearExplainer(clf, bg_t, feature_names=names)


def shap_values_matrix(explainer: shap.LinearExplainer, X_transformed: np.ndarray) -> np.ndarray:
    explanation = explainer(X_transformed)
    values = np.asarray(explanation.values)
    if values.ndim == 3:
        # Binary classifiers may return (n_samples, n_features, n_classes)
        values = values[:, :, 1]
    return values


def validate_alignment(values: np.ndarray, names: np.ndarray) -> None:
    if values.shape[1] != len(names):
        raise ValueError(
            f"SHAP dimension mismatch: values columns={values.shape[1]}, names={len(names)}"
        )
