# SHAP Explainability Report — Baseline Logistic Regression

**Generated:** 2026-10-14 (executed against live artifacts and `analytics.customer`)  
**Model artifact:** `artifacts/models/baseline_churn_pipeline.joblib`  
**Explainer:** `shap.LinearExplainer` on the fitted `LogisticRegression` step after the sklearn `ColumnTransformer`.

---

## Explanation scale

| Item | Value |
|------|--------|
| **SHAP unit** | **Log-odds** (linear model output before sigmoid) |
| **Positive class** | Churn = 1 (Yes) |
| **Churn probability** | From `predict_proba` (sigmoid of log-odds); separate from SHAP units |
| **Background sample** | Up to 500 training rows (SHAP may subsample to 100 for masker) |
| **Global explanation sample** | 1,409 test-set rows (full stratified test split from seed 42) |
| **Encoded features** | 46 (names from `preprocessor.get_feature_names_out()`) |
| **Expected value (log-odds baseline)** | -0.628 (from `artifacts/explainability/global_shap_metadata.txt`) |

**Important:** SHAP magnitudes describe **model associations**, not causal effects. Changing a feature may not change churn in practice.

---

## Global feature importance (mean |SHAP|)

Source: `artifacts/explainability/global_feature_importance.csv`

| Rank | Feature | Mean |SHAP| (log-odds) |
|------|---------|------------------------|
| 1 | tenure | 1.148 |
| 2 | TotalCharges | 0.499 |
| 3 | MonthlyCharges | 0.369 |
| 4 | Contract_Month-to-month | 0.313 |
| 5 | InternetService_Fiber optic | 0.257 |
| 6 | Contract_Two year | 0.255 |
| 7 | InternetService_DSL | 0.236 |
| 8 | PaperlessBilling_No | 0.124 |
| 9 | MultipleLines_No | 0.117 |
| 10 | PaymentMethod_Electronic check | 0.116 |

**Interpretation (associational):** Tenure and charge-related inputs dominate the linear model, followed by contract type and internet service one-hot indicators. Fiber and month-to-month categories contribute materially at the encoded-feature level.

---

## Artifacts

| Output | Path |
|--------|------|
| Feature ranking CSV | `artifacts/explainability/global_feature_importance.csv` |
| Summary plot | `artifacts/explainability/shap_summary_plot.png` |
| Bar plot | `artifacts/explainability/shap_bar_plot.png` |
| Run metadata | `artifacts/explainability/global_shap_metadata.txt` |

---

## Customer-level example (anonymized)

Demonstration record: first row of the modeling feature matrix (no `customerID` published).

| Field | Value |
|-------|--------|
| Predicted churn probability | 0.318 |
| Predicted label @ 0.5 | 0 (retained) |
| Top log-odds contributors toward churn | tenure (+1.16), Contract_Two year (+0.15), StreamingTV_Yes (+0.13) |
| Top log-odds contributors toward retention | TotalCharges (-0.42), Contract_Month-to-month (-0.36), InternetService_DSL (-0.27) |

API: `churn_intel.explain.local.explain_customer_record`

---

## Reproduction

```powershell
cd "E:\Projects\AI-Powered Customer Churn Prediction & Retention Intelligence"
$env:PYTHONPATH = "src"
python -m churn_intel.explain
```

Requires `shap>=0.53.0` (installed: **0.53.0** on Python 3.14).
