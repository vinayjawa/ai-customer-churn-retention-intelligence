# Python guide

Package root: `src/churn_intel/`. Set **`PYTHONPATH=src`** (or install editable) before running modules.

```powershell
$env:PYTHONPATH = "src"
```

## Workflow order

| Step | Module / script | Command | DB write? | File write? |
|------|-----------------|---------|-----------|-------------|
| 1 | Config | Copy `.env.example` → `.env` | No | No |
| 2 | Connection | `python -m churn_intel.connection_check` | Read-only | No |
| 3 | Ingestion | `python -m churn_intel.ingestion` | **Yes** (stg append, analytics replace) | No |
| 4 | SQL EDA export | `python scripts/run_sql_eda.py` | Read-only | CSV in `data/processed/sql_eda/` |
| 5 | Python EDA | `python -m churn_intel.analytics` | Read-only | `artifacts/eda/`, `data/processed/` |
| 6 | Train baselines | `python -m churn_intel.modeling` | Read-only | `artifacts/models/`, `artifacts/evaluation/` |
| 7 | SHAP global | `python -m churn_intel.explain` | Read-only | `artifacts/explainability/` |
| 8 | Batch score | `python -m churn_intel.scoring` | **Yes** (append scores) | Score CSV |
| 9 | Retention | `python -m churn_intel.retention` | Read-only | `data/processed/retention/` |
| 10 | Dashboard | `python -m streamlit run src/churn_intel/dashboard/app.py` | Read-only | No |

### Training vs scoring vs dashboard

- **Training** (`modeling`): fits pipeline, evaluates on held-out test split, saves **one** selected model artifact.
- **Scoring** (`scoring`): loads saved pipeline, predicts **all** customers (or `--sample N`), writes probabilities to SQL/CSV.
- **Dashboard**: displays existing mart + latest score snapshot + precomputed metrics/SHAP/retention CSVs; does **not** train or score.

## Core modules

### `churn_intel.config`

- Loads `.env` via `python-dotenv`.
- `Settings.build_database_url()` for SQLAlchemy (Windows or SQL auth).
- `PROJECT_ROOT` for artifact paths.

### `churn_intel.db`

- `create_db_engine()`, `execute_sql_file(s)`, `split_sql_batches()`.
- Used by ingestion, scoring, analytics load, dashboard.

### `churn_intel.connection_check`

- **Run:** `python -m churn_intel.connection_check`
- Verifies ODBC driver, database existence, and query to target DB.
- Read-only; prints hints without secrets.

### `churn_intel.quality.validation`

- CSV structure validation used by ingestion and unit tests.
- Not a CLI; called from `ingestion.pipeline`.

### `churn_intel.ingestion`

- **Run:** `python -m churn_intel.ingestion [--csv PATH] [--skip-ddl] [--skip-analytics]`
- Validates CSV → optional DDL 01–06 → append staging → DML refresh analytics.
- **Side effects:** staging history grows; `analytics.customer` fully replaced per run.

### `churn_intel.analytics`

- **Run:** `python -m churn_intel.analytics`
- Loads mart from SQL (`analytics.load`), computes segments/bands, writes plots and CSVs.
- Submodules: `bands`, `eda`, `load`, `metrics`, `segments`.

### `churn_intel.modeling`

- **Run:** `python -m churn_intel.modeling`
- `train.py`: stratified split, preprocessor fit on train only, three baselines, saves best by PR-AUC.
- `features.py`, `data.py`, `metrics.py`, `artifacts.py`.

### `churn_intel.explain`

- **Run:** `python -m churn_intel.explain`
- Global SHAP for logistic regression pipeline (`LinearExplainer`).
- `global_explain.py`, `local.py`, `shap_utils.py`.

### `churn_intel.scoring`

- **Run:** `python -m churn_intel.scoring [--sample N] [--no-sql]`
- `batch.py`: load model + mart, predict probabilities.
- `sql_store.py`: DDL 07 + append `ml.customer_churn_score`.
- **Side effects:** append-only score batches; optional CSV overwrite in `data/processed/retention/`.

### `churn_intel.retention`

- **Run:** `python -m churn_intel.retention`
- Joins scores with attributes; 75th percentile high-risk; rule-based recommendations in `rules.py`.
- Writes summaries under `data/processed/retention/`.

### `churn_intel.dashboard`

- **Run:** `python -m streamlit run src/churn_intel/dashboard/app.py`
- `app.py`: six pages; `data.py`: SQL + artifact loaders; `metrics.py`: KPI helpers.
- Read-only.

## Utility scripts (`scripts/`)

| Script | Purpose | Writes? |
|--------|---------|---------|
| `run_sql_eda.py` | Execute `sql/analytics/eda/*.sql` | CSV only |
| `verify_db_load.py` | Row-count verification helper | Read-only |
| `inspect_scores.py` | Inspect score table batches | Read-only |
| `phase7_consistency_audit.py` | Cross-check DB vs artifacts | JSON to `artifacts/evaluation/` |

## Tests

```powershell
python -m pytest -m "not integration" -v
```

Integration: `CHURN_DB_INTEGRATION=1` + `-m integration` — runs full ingestion (**appends staging**). See [../tests/README.md](../tests/README.md).

## Dependency note

`requirements.txt` lists `streamlit`, `plotly`, `shap` for later phases. Install only with your approval:

```powershell
python -m pip install -r requirements.txt
```
