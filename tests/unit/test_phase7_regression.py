from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from churn_intel.config import PROJECT_ROOT


@pytest.mark.parametrize(
    "relative",
    [
        "artifacts/evaluation/baseline_metrics_comparison.csv",
        "artifacts/models/baseline_model_metadata.json",
        "artifacts/explainability/global_feature_importance.csv",
    ],
)
def test_core_artifacts_exist(relative: str) -> None:
    path = PROJECT_ROOT / relative
    if not path.is_file():
        pytest.skip(f"Artifact not present locally: {relative}")
    assert path.stat().st_size > 0


def test_baseline_metrics_match_selected_logistic_regression() -> None:
    path = PROJECT_ROOT / "artifacts/evaluation/baseline_metrics_comparison.csv"
    if not path.is_file():
        pytest.skip("Metrics artifact missing")
    df = pd.read_csv(path)
    row = df.loc[df["model"] == "logistic_regression_balanced"].iloc[0]
    assert row["pr_auc"] == pytest.approx(0.6594350191363029, rel=1e-4)
    assert row["roc_auc"] == pytest.approx(0.8432444651114728, rel=1e-4)


def test_shap_row_count_matches_metadata_when_present() -> None:
    meta_path = PROJECT_ROOT / "artifacts/models/baseline_model_metadata.json"
    shap_path = PROJECT_ROOT / "artifacts/explainability/global_feature_importance.csv"
    if not meta_path.is_file() or not shap_path.is_file():
        pytest.skip("Metadata or SHAP artifact missing")
    import json

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    shap = pd.read_csv(shap_path)
    assert len(shap) == meta["feature_count_after_encoding"]
