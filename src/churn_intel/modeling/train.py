"""Train and evaluate baseline churn classifiers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from churn_intel.analytics.load import load_customer_mart
from churn_intel.config import PROJECT_ROOT
from churn_intel.modeling.data import prepare_modeling_frame
from churn_intel.modeling.features import build_preprocessor
from churn_intel.modeling.metrics import evaluate_classifier

logger = logging.getLogger(__name__)

RANDOM_SEED = 42
TEST_SIZE = 0.2
DECISION_THRESHOLD = 0.5
SELECTION_METRIC = "pr_auc"  # average precision — relevant for minority churn class

MODELS_DIR = PROJECT_ROOT / "artifacts" / "models"
EVAL_DIR = PROJECT_ROOT / "artifacts" / "evaluation"
DOCS_DIR = PROJECT_ROOT / "docs"


def _model_specs() -> dict[str, object]:
    return {
        "dummy_stratified": DummyClassifier(strategy="stratified", random_state=RANDOM_SEED),
        "logistic_regression_balanced": LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            random_state=RANDOM_SEED,
        ),
        "random_forest_balanced": RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
    }


def _feature_names_out(pipeline: Pipeline) -> list[str]:
    pre = pipeline.named_steps["preprocessor"]
    try:
        return list(pre.get_feature_names_out())
    except Exception:
        return []


def train_baselines(*, df: pd.DataFrame | None = None) -> dict[str, object]:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    raw = df if df is not None else load_customer_mart()
    X, y, validation_meta = prepare_modeling_frame(raw)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    split_meta = {
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "train_churn_prevalence": float(y_train.mean()),
        "test_churn_prevalence": float(y_test.mean()),
        "random_seed": RANDOM_SEED,
        "test_fraction": TEST_SIZE,
        "stratified": True,
    }

    preprocessor, numeric_features, categorical_features = build_preprocessor(X_train)
    results_rows: list[dict[str, object]] = []
    fitted: dict[str, Pipeline] = {}

    for name, estimator in _model_specs().items():
        pipe = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", estimator),
            ]
        )
        # Fresh preprocessor clone per model (each fit mutates the transformer).
        pre, _, _ = build_preprocessor(X_train)
        pipe.set_params(preprocessor=pre)
        pipe.fit(X_train, y_train)

        if hasattr(pipe.named_steps["classifier"], "predict_proba"):
            proba = pipe.predict_proba(X_test)[:, 1]
        else:
            proba = None
        y_pred = pipe.predict(X_test)
        metrics = evaluate_classifier(y_test, y_pred, proba)

        row = {
            "model": name,
            **{k: v for k, v in metrics.items() if k not in ("confusion_matrix", "classification_report")},
        }
        results_rows.append(row)
        fitted[name] = pipe

        cm_path = EVAL_DIR / f"{name}_confusion_matrix.json"
        cm_path.write_text(json.dumps(metrics["confusion_matrix"], indent=2), encoding="utf-8")
        report_path = EVAL_DIR / f"{name}_classification_report.txt"
        report_path.write_text(str(metrics["classification_report"]), encoding="utf-8")

    comparison = pd.DataFrame(results_rows)
    comparison_path = EVAL_DIR / "baseline_metrics_comparison.csv"
    comparison.to_csv(comparison_path, index=False)

    # Select best by PR-AUC (fallback to F1 if PR unavailable)
    scored = comparison.copy()
    if scored["pr_auc"].notna().any():
        best_idx = scored["pr_auc"].astype(float).idxmax()
        selection_reason = (
            f"Highest PR-AUC (average precision) on held-out test set at threshold {DECISION_THRESHOLD}."
        )
    else:
        best_idx = scored["f1_churn"].astype(float).idxmax()
        selection_reason = "Highest F1 for churn class (PR-AUC unavailable)."

    selected_name = str(scored.loc[best_idx, "model"])
    selected_pipeline = fitted[selected_name]

    feature_names = _feature_names_out(selected_pipeline)
    (EVAL_DIR / "selected_model_feature_names.json").write_text(
        json.dumps(feature_names, indent=2),
        encoding="utf-8",
    )

    evaluated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    metadata = {
        "evaluated_at_utc": evaluated_at,
        "data_source": "analytics.customer",
        "target": "Churn (1=churned/Yes, 0=retained/No)",
        "excluded_columns": [],
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
        "decision_threshold": DECISION_THRESHOLD,
        "selection_metric": SELECTION_METRIC,
        "selected_model": selected_name,
        "selection_reason": selection_reason,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "validation_meta": validation_meta,
        "split_meta": split_meta,
        "feature_count_after_encoding": len(feature_names),
    }
    from churn_intel.modeling.data import EXCLUDED_FEATURE_COLUMNS

    metadata["excluded_columns"] = sorted(EXCLUDED_FEATURE_COLUMNS)
    metadata["included_feature_columns"] = list(X.columns)

    meta_path = MODELS_DIR / "baseline_model_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    model_path = MODELS_DIR / "baseline_churn_pipeline.joblib"
    joblib.dump(selected_pipeline, model_path)

    _write_report(metadata, comparison, fitted, selected_name, selection_reason)

    logger.info("Selected model: %s", selected_name)
    return {
        "validation_meta": validation_meta,
        "split_meta": split_meta,
        "comparison": comparison,
        "selected_model": selected_name,
        "model_path": model_path,
        "metadata_path": meta_path,
        "comparison_path": comparison_path,
    }


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep, *rows])


def _write_report(
    metadata: dict,
    comparison: pd.DataFrame,
    fitted: dict[str, Pipeline],
    selected_name: str,
    selection_reason: str,
) -> None:
    lines = [
        "# Baseline Model Report — Customer Churn",
        "",
        f"**Generated (UTC):** {metadata['evaluated_at_utc']}",
        "",
        "## Data source and target",
        "",
        "- **Source:** `analytics.customer` on SQL Server (`ChurnIntel`).",
        "- **Target:** `Churn` — **1 = churned (Yes)**, **0 = retained (No)**.",
        "",
        "## Validation summary",
        "",
        f"- Rows: {metadata['validation_meta']['row_count']}",
        f"- Distinct customer IDs: {metadata['validation_meta']['distinct_customer_ids']}",
        f"- Churned / retained: {metadata['validation_meta']['churn_positive_count']} / "
        f"{metadata['validation_meta']['churn_negative_count']}",
        f"- NULL `TotalCharges`: {metadata['validation_meta']['null_total_charges']} "
        f"(flag `total_charges_blank`: {metadata['validation_meta']['total_charges_blank_flag']})",
        "",
        "## Features",
        "",
        "**Excluded:** " + ", ".join(f"`{c}`" for c in metadata["excluded_columns"]),
        "",
        "**Included (raw columns):** " + ", ".join(f"`{c}`" for c in metadata["included_feature_columns"]),
        "",
        "### Preprocessing",
        "",
        "- Numeric (`tenure`, `MonthlyCharges`, `TotalCharges`, `SeniorCitizen`, `total_charges_blank`): "
        "median imputation (train-only fit) + standard scaling.",
        "- Categorical (remaining service/demographic fields): most-frequent imputation + one-hot encoding "
        "(`handle_unknown='ignore'`).",
        "- `TotalCharges` NULLs imputed from training median; source table unchanged.",
        "",
        "## Train/test split",
        "",
        f"- Seed: {metadata['random_seed']}, stratified, test fraction: {metadata['test_size']}",
        f"- Train size: {metadata['split_meta']['train_size']} "
        f"(churn prevalence {metadata['split_meta']['train_churn_prevalence']:.4f})",
        f"- Test size: {metadata['split_meta']['test_size']} "
        f"(churn prevalence {metadata['split_meta']['test_churn_prevalence']:.4f})",
        "",
        "## Models",
        "",
        "- DummyClassifier (stratified)",
        "- LogisticRegression (`class_weight='balanced'`)",
        "- RandomForestClassifier (`n_estimators=200`, `class_weight='balanced'`)",
        "",
        f"Decision threshold: **{metadata['decision_threshold']}** (no test-set threshold tuning).",
        "",
        "## Metrics (held-out test set)",
        "",
        _dataframe_to_markdown(comparison),
        "",
        "## Confusion matrices (rows=true, cols=pred; labels 0=retained, 1=churn)",
        "",
    ]

    for name, pipe in fitted.items():
        _ = pipe
        cm_file = EVAL_DIR / f"{name}_confusion_matrix.json"
        cm = json.loads(cm_file.read_text(encoding="utf-8"))
        lines.append(f"### {name}")
        lines.append(f"```json\n{json.dumps(cm)}\n```")
        lines.append("")

    lines.extend(
        [
            "## Selected model",
            "",
            f"**{selected_name}** — {selection_reason}",
            "",
            "Recall vs precision: higher recall finds more at-risk customers (more outreach); "
            "higher precision reduces false alarms. Baseline comparison uses fixed 0.5 threshold.",
            "",
            "## Limitations",
            "",
            "- Not production-ready; no calibration or deployment review.",
            "- Associations in data may reflect confounding (see EDA).",
            "- No SHAP or causal inference in this phase.",
            "",
            "## Next steps (Phase 5)",
            "",
            "- SHAP explainability and retention recommendation mapping on the selected pipeline.",
            "",
        ]
    )

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = DOCS_DIR / "BASELINE_MODEL_REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    train_baselines()
    return 0
