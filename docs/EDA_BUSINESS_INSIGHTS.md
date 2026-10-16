# EDA Business Insights — IBM Telco Customer Churn

**Generated:** 2026-10-14  
**Source table:** `analytics.customer` on SQL Server database `ChurnIntel`  
**Scope:** 7,043 customers (post–Phase 2B verified mart; EDA executed against live SQL Server)

All metrics below were computed from SQL scripts under `sql/analytics/eda/` and Python EDA (`python -m churn_intel.analytics`). Results are **descriptive associations**, not causal claims.

---

## 1. Dataset scope

| Item | Value |
|------|--------|
| Table | `analytics.customer` |
| Rows analyzed | 7,043 |
| Target | `Churn` (BIT: 1 = Yes, 0 = No) |
| Identifier | `customerID` (excluded from predictors in later modeling) |
| Missing `TotalCharges` | 11 rows (`total_charges_blank = 1`, `TotalCharges IS NULL`, all `tenure = 0`) |

---

## 2. Data quality (SQL `08_data_quality_checks.sql`)

| Check | Result |
|--------|--------|
| Total rows / distinct `customerID` | 7,043 / 7,043 |
| Duplicate ID rows | 0 |
| Missing customer ID | 0 |
| Null `MonthlyCharges` / `tenure` | 0 |
| Null `TotalCharges` | 11 (documented blank-source pattern) |
| Blank total with non-zero tenure | 0 |
| Rows in `analytics.dq_load_reject` | 0 |

---

## 3. Overall churn KPIs (SQL `01_overall_churn_kpis.sql`)

| KPI | Value |
|-----|--------|
| Total customers | 7,043 |
| Churned | 1,869 |
| Retained | 5,174 |
| **Overall churn rate** | **26.54%** |
| Average tenure (months) | 32.37 |
| Avg monthly charges (USD) | 64.76 |
| Avg total charges (non-null only) | 2,283.30 |
| Blank `TotalCharges` count | 11 |

---

## 4. Highest-churn segments (rate and sample size)

### Contract (SQL `02_churn_by_contract.sql`)

| Contract | n | Churn rate |
|----------|---|------------|
| Month-to-month | 3,875 | **42.71%** |
| One year | 1,473 | 11.27% |
| Two year | 1,695 | **2.83%** |

### Tenure band (SQL `03_churn_by_tenure_band.sql`)

| Band | n | Churn rate |
|------|---|------------|
| 0–12 months | 2,186 | **47.44%** |
| 13–24 months | 1,024 | 28.71% |
| 25–48 months | 1,594 | 20.39% |
| 49+ months | 2,239 | **9.51%** |

### Payment method (SQL `04_churn_by_payment_method.sql`)

| Payment method | n | Churn rate |
|----------------|---|------------|
| Electronic check | 2,365 | **45.29%** |
| Mailed check | 1,612 | 19.11% |
| Bank transfer (automatic) | 1,544 | 16.71% |
| Credit card (automatic) | 1,522 | **15.24%** |

### Internet & support (SQL `05_churn_by_internet_and_services.sql`)

| Segment | Category | n | Churn rate |
|---------|----------|---|------------|
| InternetService | Fiber optic | 3,096 | **41.89%** |
| InternetService | DSL | 2,421 | 18.96% |
| InternetService | No | 1,526 | 7.40% |
| OnlineSecurity | No | 3,498 | **41.77%** |
| OnlineSecurity | Yes | 2,019 | 14.61% |
| TechSupport | No | 3,473 | **41.64%** |
| TechSupport | Yes | 2,044 | 15.17% |

*Note:* Categories labeled `No internet service` reflect product eligibility, not SQL NULLs.

### Monthly charge bands (SQL `06_churn_by_monthly_charges_band.sql`)

| Band (USD) | n | Churn rate |
|------------|---|------------|
| Under 35 | 1,731 | 10.86% |
| 35–49.99 | 563 | 30.73% |
| 50–69.99 | 1,158 | 20.21% |
| 70–89.99 | 1,847 | **37.95%** |
| 90+ | 1,744 | 32.86% |

---

## 5. Retention opportunity ranking (SQL `09_retention_opportunity_ranking.sql`)

Minimum segment size: **30 customers**. Ranked by **churned customer count** (volume), then churn rate.

| Rank | Segment | Value | n | Churned | Rate |
|------|---------|-------|---|---------|------|
| 1 | Contract | Month-to-month | 3,875 | 1,655 | 42.7% |
| 2 | InternetService | Fiber optic | 3,096 | 1,297 | 41.9% |
| 3 | PaymentMethod | Electronic check | 2,365 | 1,071 | 45.3% |
| 4 | TenureBand | 0–12 months | 2,186 | 1,037 | 47.4% |

Large populations drive the top opportunities; high rates in smaller bands (e.g. 35–49.99 charges, n=563) should be interpreted cautiously.

---

## 6. Practical recommendations (hypothesis-generating)

1. **Early-tenure retention programs** — Nearly half of customers in the first 12 months churn (47.4%, n=2,186). Onboarding, usage checks, and proactive support in year one are priority areas to *test*, not proven levers.
2. **Month-to-month contract offers** — Highest contract-type churn (42.7%, n=3,875). Pilot structured migration to longer contracts with transparent benefits; monitor take-up and churn, avoiding pressure tactics.
3. **Payment experience** — Electronic check users show 45.3% churn (n=2,365) vs ~15–17% for automatic card/bank pay. Encourage autopay with clear billing UX; treat as correlation until validated experimentally.
4. **Fiber + add-on gaps** — Fiber optic (41.9% churn) combined with lack of Online Security / Tech Support (both ~41.6% churn when “No”) suggests bundling security/support messaging for high-speed customers — subject to A/B testing.
5. **Mid/high monthly charge bands** — 70–89.99 USD band shows 38.0% churn (n=1,847). Review pricing satisfaction and competitive positioning for this cohort.

---

## 7. Limitations and caveats

- **Correlation ≠ causation** — Demographics and product flags may overlap (e.g. fiber vs contract type).
- **Snapshot data** — No time-to-event modeling yet; tenure patterns are cross-sectional.
- **Missing total charges** — 11 new customers (tenure 0); excluded from total-charge averages but included in counts and other fields.
- **Small segments** — Bands with n < 30 are filtered from the SQL ranking script; other small groups may still show volatile rates.
- **No ML in this phase** — Patterns may change after multivariate modeling (Phase 4).

---

## 8. Reproduction

**Prerequisites:** `.env` configured; `ChurnIntel` populated; `PYTHONPATH=src`.

```powershell
cd <project-root>
$env:PYTHONPATH = "src"

# Export SQL EDA results to data/processed/sql_eda/
python scripts/run_sql_eda.py

# Python EDA: plots -> artifacts/eda/, tables -> data/processed/
python -m churn_intel.analytics

# Tests
python -m pytest -m "not integration" -v
```

**SQL scripts:** `sql/analytics/eda/01_overall_churn_kpis.sql` … `09_retention_opportunity_ranking.sql`

**Python modules:** `src/churn_intel/analytics/` (`load.py`, `bands.py`, `metrics.py`, `segments.py`, `eda.py`)
