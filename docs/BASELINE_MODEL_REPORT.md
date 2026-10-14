# Baseline Model Report — Customer Churn

**Generated (UTC):** 2026-10-14T10:28:20+00:00

## Data source and target

- **Source:** `analytics.customer` on SQL Server (`ChurnIntel`).
- **Target:** `Churn` — **1 = churned (Yes)**, **0 = retained (No)**.

## Validation summary

- Rows: 7043
- Distinct customer IDs: 7043
- Churned / retained: 1869 / 5174
- NULL `TotalCharges`: 11 (flag `total_charges_blank`: 11)

## Features

**Excluded:** `Churn`, `ChurnLabel`, `customerID`, `ingest_batch_id`, `loaded_at_utc`

**Included (raw columns):** `gender`, `SeniorCitizen`, `Partner`, `Dependents`, `tenure`, `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges`, `total_charges_blank`

### Preprocessing

- Numeric (`tenure`, `MonthlyCharges`, `TotalCharges`, `SeniorCitizen`, `total_charges_blank`): median imputation (train-only fit) + standard scaling.
- Categorical (remaining service/demographic fields): most-frequent imputation + one-hot encoding (`handle_unknown='ignore'`).
- `TotalCharges` NULLs imputed from training median; source table unchanged.

## Train/test split

- Seed: 42, stratified, test fraction: 0.2
- Train size: 5634 (churn prevalence 0.2654)
- Test size: 1409 (churn prevalence 0.2654)

## Models

- DummyClassifier (stratified)
- LogisticRegression (`class_weight='balanced'`)
- RandomForestClassifier (`n_estimators=200`, `class_weight='balanced'`)

Decision threshold: **0.5** (no test-set threshold tuning).

## Metrics (held-out test set)

| model | accuracy | precision_churn | recall_churn | f1_churn | test_churn_prevalence | roc_auc | pr_auc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dummy_stratified | 0.6217175301632364 | 0.2891246684350133 | 0.2914438502673797 | 0.29027962716378164 | 0.2654364797728886 | 0.5162533260998735 | 0.2723402566824383 |
| logistic_regression_balanced | 0.7402413058907026 | 0.5069204152249135 | 0.7834224598930482 | 0.615546218487395 | 0.2654364797728886 | 0.8432444651114728 | 0.6594350191363029 |
| random_forest_balanced | 0.7771469127040455 | 0.572463768115942 | 0.6336898395721925 | 0.6015228426395939 | 0.2654364797728886 | 0.8249928957090082 | 0.6079102316487504 |

## Confusion matrices (rows=true, cols=pred; labels 0=retained, 1=churn)

### dummy_stratified
```json
[[767, 268], [265, 109]]
```

### logistic_regression_balanced
```json
[[750, 285], [81, 293]]
```

### random_forest_balanced
```json
[[858, 177], [137, 237]]
```

## Selected model

**logistic_regression_balanced** — Highest PR-AUC (average precision) on held-out test set at threshold 0.5.

Recall vs precision: higher recall finds more at-risk customers (more outreach); higher precision reduces false alarms. Baseline comparison uses fixed 0.5 threshold.

## Limitations

- Not production-ready; no calibration or deployment review.
- Associations in data may reflect confounding (see EDA).
- No SHAP or causal inference in this phase.

## Next steps (Phase 5)

- SHAP explainability and retention recommendation mapping on the selected pipeline.
