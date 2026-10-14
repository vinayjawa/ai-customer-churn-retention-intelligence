# Retention Intelligence — Phase 5

**Generated:** 2026-10-14 (executed on live scores + `analytics.customer`)  
**Model version:** `baseline_logistic_v1`  
**Scores:** `data/processed/retention/customer_churn_scores.csv` (7,043 rows)  
**SQL history:** append-only inserts into `ml.customer_churn_score` (7,043 rows written in initial Phase 5 run)

---

## Prioritization framework

1. **Predicted risk** — average or individual `churn_probability` from the baseline pipeline (not causal).
2. **Segment volume** — count of customers in each segment (minimum 30 for EDA-style segments; retention export uses all scored customers).
3. **High-risk flag** — customers at or above the **75th percentile** of predicted probability (**threshold ≈ 0.72** from `retention_analysis_metadata.txt`).
4. **Observed churn** — historical `Churn` label shown for context only; it is **not** the same as predicted risk.

**ROI / CLV / campaign conversion:** **Unavailable** — not estimated in this phase.

---

## High-risk segments (by predicted risk volume)

Source: `data/processed/retention/retention_segment_summary.csv` (sorted by `high_risk_count`)

| Segment | Value | Customers | Avg predicted risk | High-risk count | Actual churn rate (observed) |
|---------|-------|-----------|--------------------|-----------------|------------------------------|
| Contract | Month-to-month | 3,875 | 0.630 | 1,758 | 42.7% |
| TechSupport | No | 3,473 | 0.607 | 1,608 | 41.6% |
| OnlineSecurity | No | 3,498 | 0.603 | 1,608 | 41.8% |
| PaymentMethod | Electronic check | 2,365 | 0.643 | 1,295 | 45.3% |
| TenureBand | 0–12 months | 2,186 | 0.645 | 1,116 | 47.4% |

Predicted risk and observed churn align directionally but are **not** identical metrics.

---

## Recommendation hypotheses (rule mapping)

Source: `data/processed/retention/retention_recommendation_summary.csv`  
Eligible population: customers flagged **high risk** (top quartile of predicted probability).

| Code | Hypothesis | Eligible high-risk customers |
|------|------------|------------------------------|
| CONTRACT_REVIEW | Month-to-month contract discussion | 1,758 |
| SECURITY_REVIEW | Online security outreach | 1,608 |
| TECH_SUPPORT_INFO | Tech support information | 1,608 |
| PAYMENT_EXPERIENCE | Payment / electronic check experience | 1,295 |
| EARLY_LIFE_SUPPORT | Early tenure onboarding support | 1,116 |

These are **testable outreach ideas**, not guarantees of churn reduction.

---

## Outputs (no customer IDs in segment/recommendation summaries)

| File | Purpose |
|------|---------|
| `customer_churn_scores.csv` | Internal join key `customerID`, probability, label, model version, timestamp |
| `high_risk_customers_anonymized_top100.csv` | Top 100 ranks without `customerID` |
| `retention_segment_summary.csv` | Aggregated segment KPIs |
| `retention_recommendation_summary.csv` | Aggregated recommendation eligibility |
| `retention_analysis_metadata.txt` | Thresholds and notes |

---

## SQL score storage

- **Table:** `ml.customer_churn_score` (extended via `sql/ddl/07_ml_scoring_columns.sql` with `predicted_churn`, `model_version`).
- **Behavior:** **Append** new score rows each run (history preserved).
- **Registry:** `ml.model_registry` row for `logistic_regression_balanced` / `baseline_logistic_v1`.

---

## Reproduction

```powershell
$env:PYTHONPATH = "src"
python -m churn_intel.scoring          # add --no-sql or --sample 500 for options
python -m churn_intel.retention
```
