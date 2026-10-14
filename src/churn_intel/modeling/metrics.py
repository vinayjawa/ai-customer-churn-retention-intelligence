"""Evaluation metrics for binary churn classification."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_classifier(
    y_true,
    y_pred,
    y_proba=None,
    *,
    positive_label: int = 1,
) -> dict[str, object]:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    metrics: dict[str, object] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_churn": float(
            precision_score(y_true, y_pred, pos_label=positive_label, zero_division=0)
        ),
        "recall_churn": float(
            recall_score(y_true, y_pred, pos_label=positive_label, zero_division=0)
        ),
        "f1_churn": float(f1_score(y_true, y_pred, pos_label=positive_label, zero_division=0)),
        "test_churn_prevalence": float(np.mean(y_true == positive_label)),
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(
            y_true, y_pred, target_names=["retained_0", "churn_1"], zero_division=0
        ),
    }
    if y_proba is not None:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        metrics["pr_auc"] = float(average_precision_score(y_true, y_proba))
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None
    return metrics
