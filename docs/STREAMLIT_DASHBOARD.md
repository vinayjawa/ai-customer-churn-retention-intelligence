# Streamlit Dashboard — Churn Intelligence

**Purpose:** Local portfolio demonstration (not production-ready).

## Launch

```powershell
cd "E:\Projects\AI-Powered Customer Churn Prediction & Retention Intelligence"
$env:PYTHONPATH = "src"
python -m streamlit run src/churn_intel/dashboard/app.py
```

Stop with `Ctrl+C` in the terminal.

## Prerequisites

- Python 3.14+ with `streamlit`, `plotly`, and project dependencies (`pip install -r requirements.txt`).
- `.env` configured for SQL Server (Windows auth) — **do not commit or share**.
- Phase 2–5 artifacts present (customer mart, scores, SHAP CSV, retention CSVs, model metrics CSV).

## Pages

| Page | Data sources |
|------|----------------|
| Executive Overview | `analytics.customer` (SQL), latest score snapshot |
| Churn Analytics | `analytics.customer` — **observed** churn rates |
| Churn Risk | Latest scores + customer attributes |
| Model Performance | `artifacts/evaluation/baseline_metrics_comparison.csv` |
| SHAP Explainability | `artifacts/explainability/*` (CSV + PNG) |
| Retention Intelligence | `data/processed/retention/*` summaries |

## Latest score snapshot (append-only SQL history)

`ml.customer_churn_score` stores **append-only** rows. The dashboard:

1. Loads score history (SQL by default; CSV fallback if SQL fails).
2. Selects rows with the **maximum `scored_at_utc`**.
3. Deduplicates by `customerID` within that batch if needed.
4. Warns if batch size differs from the expected 7,043 customer snapshot.

**Verified (2026-10-14):** one batch at `2026-10-14 10:36:21 UTC`, 7,043 rows, version `baseline_logistic_v1`.

## Threshold semantics

| Concept | Definition |
|---------|------------|
| **Predicted churn label** | `churn_probability >= 0.5` (model threshold) |
| **High-risk flag (retention)** | `churn_probability >= 75th percentile` within the scored population (~**0.701**, **1,761** customers at last verification) |

High-risk is **not** the same as the 0.5 classification threshold.

## Privacy

- Default tables exclude `customerID`.
- Anonymized top-risk table uses `anonymized_rank` only.
- Dashboard performs **read-only** SQL; no scoring, training, or writes on startup.

## Limitations

- Predictions are not confirmed future churn.
- SHAP artifacts are log-odds based (global, precomputed).
- No ROI / CLV / campaign effectiveness claims.
- Filters apply to customer snapshots; metric CSVs on Model/Retention pages are global artifacts unless regenerated.
