# SQL guide

All paths are relative to the project root. **Do not execute write scripts** during documentation-only review.

## Schemas

Created in `sql/ddl/01_schemas.sql`: `stg`, `analytics`, `ml`, `retention`.

## Recommended execution order

### A. One-time / idempotent database initialization

Run when the database is empty or you need objects created. **Ingestion runs these automatically** unless you pass `--skip-ddl`.

| Order | File | Type | Creates / alters | Writes data? |
|------:|------|------|------------------|--------------|
| 1 | `sql/ddl/01_schemas.sql` | DDL | Four schemas | No |
| 2 | `sql/ddl/02_stg_telco_customer_churn.sql` | DDL | `stg.telco_customer_churn` | No |
| 3 | `sql/ddl/03_analytics_customer.sql` | DDL | `analytics.customer`, `analytics.dq_load_reject` | No |
| 4 | `sql/ddl/04_ml_schema.sql` | DDL | `ml.model_registry`, `ml.customer_churn_score` | No |
| 5 | `sql/ddl/05_retention_schema.sql` | DDL | Retention schema placeholder | No |
| 6 | `sql/ddl/06_analytics_views.sql` | DDL | `analytics.v_customer_churn` | No |

**Source of truth for order:** `churn_intel.ingestion.pipeline.ddl_script_paths()`.

### B. Optional ML scoring column migration

| File | When | Effect |
|------|------|--------|
| `sql/ddl/07_ml_scoring_columns.sql` | Before / during first Phase 5 score | Adds `predicted_churn`, `model_version` to `ml.customer_churn_score` if missing |

Applied automatically by `churn_intel.scoring.sql_store.apply_scoring_ddl()` when you run batch scoring.

### C. Data load (writes data)

| Step | Mechanism | Effect |
|------|-----------|--------|
| Staging insert | `python -m churn_intel.ingestion` | **Appends** rows to `stg.telco_customer_churn` with new `ingest_batch_id` |
| Analytics refresh | `sql/dml/01_refresh_analytics_from_stg.sql` (via ingestion) | **Deletes all rows** in `analytics.customer`, then reloads from the current batch; rejects go to `analytics.dq_load_reject` |

### D. Read-only analytics (safe to re-run)

| File | Purpose | Output / use |
|------|---------|--------------|
| `sql/analytics/01_dq_summary.sql` | Row counts, churn counts, reject summary | Manual SSMS check after load |
| `sql/analytics/02_v_customer_churn.sql` | View definition (also in ddl 06) | Convenient `ChurnLabel` column |
| `sql/analytics/eda/01_overall_churn_kpis.sql` | Overall KPIs | Business: baseline churn rate |
| `sql/analytics/eda/02_churn_by_contract.sql` | Churn by contract type | Month-to-month vs term |
| `sql/analytics/eda/03_churn_by_tenure_band.sql` | Churn by tenure bands | Early-life churn |
| `sql/analytics/eda/04_churn_by_payment_method.sql` | Churn by payment method | Electronic check pattern |
| `sql/analytics/eda/05_churn_by_internet_and_services.sql` | Internet + add-on services | Fiber, security, support |
| `sql/analytics/eda/06_churn_by_monthly_charges_band.sql` | Churn by charge bands | Price sensitivity segments |
| `sql/analytics/eda/07_churn_by_demographics.sql` | Gender, senior, partner, dependents | Demographic splits |
| `sql/analytics/eda/08_data_quality_checks.sql` | NULLs, blanks, duplicates | QA |
| `sql/analytics/eda/09_retention_opportunity_ranking.sql` | Segment ranking by churn rate × volume | Prioritization input |

**Runner:** `python scripts/run_sql_eda.py` — read-only SELECTs; writes CSVs to `data/processed/sql_eda/` (filesystem only).

## Model scoring (SQL writes)

Not defined as standalone `.sql` files beyond DDL. Python module `churn_intel.scoring`:

- Inserts into `ml.model_registry` if needed
- **Appends** rows to `ml.customer_churn_score` (history preserved; dashboard uses latest `scored_at_utc`)

## Dependencies between objects

```text
stg.telco_customer_churn  --(dml refresh)-->  analytics.customer
analytics.customer        --(SELECT)-->       Python modeling / dashboard
ml.model_registry         --(FK)-->           ml.customer_churn_score
```

## Manual execution in SSMS

1. Connect to your instance; use database `ChurnIntel` (or name in `.env`).
2. Run DDL scripts **01 → 06** in order (or use ingestion without `--skip-ddl`).
3. Run EDA scripts individually or use `scripts/run_sql_eda.py`.
4. Avoid running `01_refresh_analytics_from_stg.sql` manually unless you replace `__BATCH_ID__` with a real staging batch GUID.

## Python counterparts

| SQL area | Python module |
|----------|----------------|
| Ingestion + DML refresh | `churn_intel.ingestion` |
| EDA export | `scripts/run_sql_eda.py`, `churn_intel.analytics` |
| Modeling (reads mart) | `churn_intel.modeling` |
| Scoring (writes ml) | `churn_intel.scoring` |
| Dashboard reads | `churn_intel.dashboard.data` |

See [PYTHON_GUIDE.md](PYTHON_GUIDE.md).
