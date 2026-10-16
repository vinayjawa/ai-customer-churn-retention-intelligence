# Dashboard guide

**App entry:** `src/churn_intel/dashboard/app.py`  
**Launch:** see [SETUP_GUIDE.md](SETUP_GUIDE.md).

The dashboard is a **read-only** portfolio demo. It does not train models or write scores on startup.

## Pages (six)

| Page | What it shows | Primary data source |
|------|---------------|---------------------|
| **Executive Overview** | Customer count, **historical** churn rate, tenure/charges, observed churn counts, **predicted churn @ 0.5**, **high-risk** count | SQL `analytics.customer` + latest score batch |
| **Churn Analytics** | Bar charts of **observed** churn rate by contract, tenure band, payment, internet, security, support, charge band | Filtered `analytics.customer` |
| **Churn Risk** | Probability histogram, predicted churn/retained @ 0.5, high-risk count, avg risk by contract, anonymized top-risk table | Scores merged to customers + retention CSV |
| **Model Performance** | Metrics table and bar chart (ROC-AUC, PR-AUC, F1) | `artifacts/evaluation/baseline_metrics_comparison.csv` |
| **SHAP Explainability** | Top 15 features bar chart + saved PNG plots | `artifacts/explainability/*` |
| **Retention Intelligence** | Metadata text, segment summary, recommendation eligibility | `data/processed/retention/*.csv` |

## KPI definitions

| KPI | Definition |
|-----|------------|
| Historical churn rate | Share of rows with observed `Churn = 1` in the filtered customer snapshot |
| Predicted churn @ 0.5 | Count where `churn_probability >= 0.5` |
| High-risk (top 25% risk) | Count where probability ≥ **75th percentile** within the **latest score batch** (same rule as Phase 5 retention) |
| Avg tenure / monthly charges | Descriptive stats on filtered customers |

**Important:** “Churn Analytics” uses **observed** labels. “Churn Risk” and overview risk KPIs use **model scores**.

## Sidebar

- **Navigation:** radio buttons for the six pages.
- **Load scores from SQL Server:** when enabled, loads full score history from `ml.customer_churn_score` and keeps only the latest `scored_at_utc` batch; on failure, falls back to CSV with a warning.
- **Refresh cached data:** clears Streamlit `@st.cache_data` (reload from SQL/files).
- **Filters:** Contract, Payment method, Internet service, Tenure band — apply to customer-based pages; scores are filtered to matching `customerID`s on overview/risk.

## CSV fallback behavior

Implemented in `churn_intel.dashboard.data.load_scores`:

1. If `prefer_sql=True`, try SQL.
2. On any exception, log warning and read `data/processed/retention/customer_churn_scores.csv`.
3. Latest batch selection uses the same `select_latest_score_batch()` logic for both sources.

**Verify SQL mode:** Executive Overview info box shows `source: sql_server`.

## Privacy

- Display tables use `sanitize_display_frame()` to drop `customerID`, `ingest_batch_id`, `loaded_at_utc`.
- Anonymized top-risk table uses rank columns only (from `high_risk_customers_anonymized_top100.csv`).

## Dependencies

- Working SQL for **customer** data (required).
- Scores: SQL and/or score CSV from Phase 5.
- Model/SHAP/retention pages need corresponding artifacts under `artifacts/` and `data/processed/retention/`.

## Known limitations

- Model Performance and Retention pages show **global** artifacts — not re-filtered by sidebar dimensions (except where merged on Churn Risk).
- SHAP PNGs are static Phase 5 outputs (log-odds).
- No ROI, CLV, or campaign tracking.
- Interactive behavior beyond data load was not exhaustively automated-tested; verify manually after setup.

## Streamlit screenshots

Six PNG captures live under [screenshots/](screenshots/README.md) and are linked from the root README. They document layout and sample KPIs from a prior local session; re-capture after material dashboard or data changes.

Legacy short notes: [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md).
