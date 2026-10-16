# Model documentation

Values below come from `artifacts/models/baseline_model_metadata.json` and `artifacts/evaluation/baseline_metrics_comparison.csv` produced by `python -m churn_intel.modeling` on the local dataset snapshot.

## Prediction target

- **Column:** `Churn` in `analytics.customer` (1 = churned / Yes, 0 = retained / No).
- **Excluded from features:** `Churn`, `ChurnLabel`, `customerID`, `ingest_batch_id`, `loaded_at_utc`.

## Features and preprocessing

**Numeric (5):** `tenure`, `MonthlyCharges`, `TotalCharges`, `SeniorCitizen`, `total_charges_blank` (flag for blank `TotalCharges` at tenure 0).

**Categorical (15):** gender, Partner, Dependents, PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling, PaymentMethod.

**Pipeline:** sklearn `ColumnTransformer` — imputation + scaling for numeric; one-hot encoding for categorical (`handle_unknown='ignore'`). **46** columns after encoding.

Preprocessor is **fit on training split only** (see unit tests in `tests/unit/test_modeling.py`).

## Train / test split

| Setting | Value |
|---------|--------|
| Rows | 7,043 |
| Test fraction | 0.2 (1,409 test / 5,634 train) |
| Stratified | Yes |
| Random seed | 42 |

## Algorithms compared

1. `DummyClassifier(strategy='stratified')` — baseline.
2. `LogisticRegression(class_weight='balanced', max_iter=2000)` — **selected**.
3. `RandomForestClassifier(n_estimators=200, class_weight='balanced')`.

**Selection rule:** highest **PR-AUC** (average precision) on held-out test set at probability threshold **0.5**.

## Test-set metrics (held-out)

| Model | Accuracy | Precision (churn) | Recall (churn) | F1 | ROC-AUC | PR-AUC |
|-------|----------|-------------------|----------------|-----|---------|--------|
| Dummy stratified | 0.622 | 0.289 | 0.291 | 0.290 | 0.516 | 0.272 |
| **Logistic regression (balanced)** | **0.740** | **0.507** | **0.783** | **0.616** | **0.843** | **0.659** |
| Random forest (balanced) | 0.777 | 0.572 | 0.634 | 0.602 | 0.825 | 0.608 |

**Why logistic regression:** best PR-AUC for the minority churn class; higher recall at the cost of precision vs random forest — documented trade-off for “flag more potential churners.”

Detailed narrative: [BASELINE_MODEL_REPORT.md](BASELINE_MODEL_REPORT.md).

## Threshold logic

| Use | Threshold | Where |
|-----|-----------|--------|
| Binary predicted label | **0.5** on `churn_probability` | Scoring, metadata, dashboard “Predicted churn @ 0.5” |
| Retention high-risk flag | **≥ 75th percentile** of scored population (example ~0.701 when 7,043 customers scored) | `retention`, dashboard high-risk KPIs |

High-risk is **not** the same as predicted churn at 0.5.

## Artifacts

| File | Content |
|------|---------|
| `artifacts/models/baseline_churn_pipeline.joblib` | Fitted pipeline |
| `artifacts/models/baseline_model_metadata.json` | Features, split, selection |
| `artifacts/evaluation/baseline_metrics_comparison.csv` | Table above |
| Per-model confusion matrices / classification reports | Same folder |

## SHAP (explainability)

- **Module:** `python -m churn_intel.explain`
- **Explainer:** SHAP `LinearExplainer` on the logistic regression step; global values in **log-odds** space for churn class.
- **Feature alignment:** 46 SHAP rows match encoded pipeline features (verified in tests).

See [SHAP_EXPLAINABILITY_REPORT.md](SHAP_EXPLAINABILITY_REPORT.md).

## Limitations and validation notes

- **Historical labels:** model learns past churn, not future certainty.
- **Single time snapshot:** no temporal cross-validation or walk-forward validation.
- **Associations ≠ causation:** high SHAP for contract type does not prove changing contract reduces churn.
- **Class imbalance:** metrics emphasize PR-AUC and recall; precision on churn class is moderate (~0.51).
- **Data leakage controls:** target and IDs excluded; preprocessor fit on train split only; no explicit future features in schema.
- **Blank TotalCharges:** handled via NULL + `total_charges_blank` flag (11 rows at tenure 0 in reference data).

Do **not** retrain or overwrite artifacts unless you explicitly intend to refresh results (`python -m churn_intel.modeling`).
