"""Global SHAP analysis and plots."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split

from churn_intel.analytics.load import load_customer_mart
from churn_intel.config import PROJECT_ROOT
from churn_intel.explain.shap_utils import (
    EXPLANATION_SCALE,
    build_linear_explainer,
    feature_names,
    shap_values_matrix,
    transformed_matrix,
    validate_alignment,
)
from churn_intel.modeling.artifacts import load_metadata, load_pipeline
from churn_intel.modeling.data import prepare_modeling_frame
from churn_intel.modeling.train import RANDOM_SEED, TEST_SIZE

GLOBAL_SAMPLE_SIZE = 2000
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "explainability"


def run_global_shap_analysis(*, df: pd.DataFrame | None = None) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = load_pipeline()
    _ = load_metadata()

    raw = df if df is not None else load_customer_mart()
    X, y, _ = prepare_modeling_frame(raw)
    X_train, X_test, _, _ = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )

    explainer = build_linear_explainer(pipeline, X_train)
    names = feature_names(pipeline)

    sample = X_test if len(X_test) <= GLOBAL_SAMPLE_SIZE else X_test.sample(
        n=GLOBAL_SAMPLE_SIZE, random_state=RANDOM_SEED
    )
    sample_t = transformed_matrix(pipeline, sample)
    values = shap_values_matrix(explainer, sample_t)
    validate_alignment(values, names)

    mean_abs = np.abs(values).mean(axis=0)
    importance = (
        pd.DataFrame({"feature": names, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
    csv_path = OUTPUT_DIR / "global_feature_importance.csv"
    importance.to_csv(csv_path, index=False)

    shap.summary_plot(values, sample_t, feature_names=names, show=False)
    fig = plt.gcf()
    summary_path = OUTPUT_DIR / "shap_summary_plot.png"
    fig.savefig(summary_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    shap.plots.bar(explainer(sample_t[: min(500, len(sample_t))]), show=False)
    fig = plt.gcf()
    bar_path = OUTPUT_DIR / "shap_bar_plot.png"
    fig.savefig(bar_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    meta_path = OUTPUT_DIR / "global_shap_metadata.txt"
    meta_path.write_text(
        "\n".join(
            [
                f"explanation_scale={EXPLANATION_SCALE}",
                f"sample_rows={len(sample)}",
                f"feature_count={len(names)}",
                f"expected_value_log_odds={explainer.expected_value}",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "importance_csv": csv_path,
        "summary_plot": summary_path,
        "bar_plot": bar_path,
        "metadata": meta_path,
    }
