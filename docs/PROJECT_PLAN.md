# Project Plan — AI-Powered Customer Churn Prediction & Retention Intelligence

**Version:** Phase 1 (planning only)  
**Last updated:** 2026-10-14  
**Python environment (inspected):** 3.14.7 (`C:\Users\admin\AppData\Local\Python\pythoncore-3.14-64\python.exe`)

---

## 1. Vision

Deliver a portfolio-grade, end-to-end churn analytics system that:

1. Lands telco customer data in **Microsoft SQL Server**.
2. Runs **SQL data-quality checks** and descriptive analytics.
3. Uses **Python** for EDA, feature engineering, and ML (scikit-learn / XGBoost).
4. Explains predictions with **SHAP** and maps scores to **retention recommendations**.
5. Exposes insights through a **Streamlit** dashboard (and optionally a thin **FastAPI** layer for scoring).
6. Ships with **pytest**, documentation, and GitHub-ready layout (**raw data excluded** from Git).

No model training or production deployment occurs in Phase 1.

---

## 2. Proposed repository layout

```
AI-Powered Customer Churn Prediction & Retention Intelligence/
├── data/                          # NOT committed (see .gitignore in Phase 2)
│   ├── raw/                       # Symlink or copy policy for Kaggle CSV
│   └── processed/                 # Parquet/CSV exports from pipelines
├── docs/
│   ├── PROJECT_PLAN.md            # This file
│   └── DATASET_PROFILE.md         # Measured dataset inspection
├── sql/
│   ├── ddl/                       # CREATE TABLE, indexes, constraints
│   ├── dml/                       # Seed/staging load scripts
│   └── analytics/                 # Quality checks, cohort KPIs, churn SQL
├── src/
│   └── churn_intel/
│       ├── __init__.py
│       ├── config/                # Settings from env (no secrets in code)
│       ├── db/                    # SQLAlchemy engine, sessions, repositories
│       ├── ingestion/             # CSV → SQL Server
│       ├── quality/               # Checks (Python + SQL parity)
│       ├── analytics/             # EDA helpers, SQL result consumers
│       ├── features/              # Sklearn pipelines, encoders
│       ├── models/                # Train, evaluate, persist artifacts
│       ├── explain/               # SHAP, recommendation rules
│       ├── serving/               # Optional FastAPI predict endpoints
│       └── dashboard/             # Streamlit app
├── tests/
│   ├── unit/
│   ├── integration/               # DB tests (marked, require SQL Server)
│   └── conftest.py
├── notebooks/                     # Optional exploratory only (not source of truth)
├── artifacts/                     # Models, metrics, SHAP plots (gitignored or DVC)
├── .env.example                   # Variable names only
├── .gitignore
├── pyproject.toml                 # Or requirements.txt + optional constraints
├── README.md
└── WA_Fn-UseC_-Telco-Customer-Churn.csv   # Current location: project root (move to data/raw in Phase 2)
```

**Design principles**

- **Single package** (`churn_intel`) importable from CLI, tests, Streamlit, and FastAPI.
- **SQL as source of truth** for curated customer tables; Python reads via SQLAlchemy for ML.
- **Config via environment** (`CHURN_DB_URL`, etc.); never commit credentials.
- **Idempotent ingestion** (truncate/reload staging or MERGE into mart).
- **Artifact versioning** (model + feature schema JSON alongside pickle/joblib).

---

## 3. Technology choices

| Layer | Choice | Notes |
|-------|--------|-------|
| Database | SQL Server | User-provided instance |
| DB access | SQLAlchemy 2.x + pyodbc | ODBC Driver 17 or 18 for SQL Server |
| ETL / analytics | pandas, numpy | Already installed |
| Viz | matplotlib, seaborn | EDA reports |
| ML | scikit-learn, XGBoost | Baseline + gradient boosting |
| Explainability | SHAP | TreeExplainer for XGBoost / compatible models |
| Dashboard | Streamlit | Primary UI |
| API | FastAPI (optional) | Justified if dashboard and external clients need shared scoring service |
| Tests | pytest | Unit + optional integration |
| VCS | Git + GitHub | Git was **not** on PATH at Phase 1 inspection |

### 3.1 Python packages

**Already installed (measured)**

| Package | Version |
|---------|---------|
| pandas | 3.0.6 |
| numpy | 2.5.3 |
| scikit-learn | 1.9.1 |
| matplotlib | 3.11.2 |
| seaborn | 0.13.2 |
| streamlit | 1.64.0 |
| openpyxl | 3.1.5 |

**Recommended to install in Phase 2** (compatible with Python 3.14; pin after first successful install):

```
SQLAlchemy>=2.0.54,<2.2
pyodbc>=5.3.0
xgboost>=2.1.0
shap>=0.53.0
pytest>=8.0
pytest-cov>=5.0
python-dotenv>=1.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic-settings>=2.0
```

Install only after you approve; record exact versions in `requirements.txt` or `pyproject.toml`.

---

## 4. SQL Server prerequisites (user / infra)

Before database implementation (Phase 2), confirm:

| Prerequisite | Status at Phase 1 |
|--------------|-------------------|
| SQL Server instance (Express/Developer/Standard) | **Unknown** — you must confirm |
| Instance name / host / port | **Required** (e.g. `localhost\SQLEXPRESS`) |
| Authentication | **Required** — Windows auth vs SQL login |
| Database name | **Proposed:** `ChurnIntel` (confirm or rename) |
| ODBC Driver 17 or 18 for SQL Server | **Required** for pyodbc |
| Firewall / TCP enabled for SQL Server | If connecting remotely |
| Login permissions | CREATE TABLE, INSERT, SELECT at minimum |

**Connection string pattern (no secrets in repo):**

```
mssql+pyodbc://<user>:<password>@<server>/<database>?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

Use `.env` locally; document variables in `.env.example` only.

---

## 5. Phased delivery

### Phase 1 — Inspection & planning ✅ (current)

**Deliverables**

- [x] Folder inspection and dataset identification
- [x] `docs/DATASET_PROFILE.md`
- [x] `docs/PROJECT_PLAN.md`

**Verification**

- Dataset profile numbers match independent re-run of read-only Python profile
- No changes to raw CSV
- No ML training or package installs without approval

---

### Phase 2 — Repository scaffold & SQL Server foundation

**Goals**

- Initialize Git, `.gitignore` (exclude `data/raw/*.csv`, `.env`, `artifacts/`)
- Create package layout under `src/churn_intel`
- DDL for staging + core `dim_customer` / `fact_customer_snapshot` (or simplified single mart table)
- Ingestion script: CSV → SQL Server
- SQL data-quality script (nulls, duplicates, domain checks, churn balance)

**Deliverables**

- Working load of 7,043 rows into SQL Server
- Documented connection setup in README
- pytest for pure-Python quality helpers (DB tests optional/skipped without env)

**Verification**

- Row count in SQL = 7,043
- Zero duplicate `customerID`
- 11 NULL/empty TotalCharges aligned with tenure 0
- Churn distribution matches profile

**Blockers to resolve before starting**

- SQL Server connection details (see section 6)
- Whether to **move** CSV to `data/raw/` (copy only; never delete original without explicit approval)

---

### Phase 3 — SQL analytics & Python EDA

**Goals**

- SQL reports: churn by contract, tenure bands, payment method, services
- Python EDA module producing saved figures to `artifacts/eda/`
- Document business questions and findings in `docs/EDA_SUMMARY.md`

**Verification**

- SQL metrics reproducible from documented queries
- EDA notebook/script runs headless

---

### Phase 4 — Feature engineering & ML baseline

**Goals**

- Sklearn `ColumnTransformer` pipeline (numeric + categorical)
- Train/validation split with stratified `Churn`
- Models: logistic regression (interpretable baseline), random forest, XGBoost
- Metrics: ROC-AUC, precision/recall, confusion matrix, calibration (reported honestly on holdout only)

**Verification**

- Reproducible training CLI with fixed `random_state`
- Metrics JSON saved under `artifacts/metrics/`
- No test-set leakage in feature building

---

### Phase 5 — SHAP & retention intelligence

**Goals**

- Global and local SHAP for best validated model
- Rule-based or score-driven **retention recommendations** (e.g. contract upgrade, tech support, payment method)
- Export customer-level risk table (customerID, probability, top drivers, recommendation)

**Verification**

- SHAP outputs for sample customers documented
- Recommendations traceable to feature values (no fabricated business outcomes)

---

### Phase 6 — Streamlit dashboard (+ optional FastAPI)

**Goals**

- Streamlit: KPIs, segment filters, risk list, explainability view
- Optional FastAPI: `POST /predict` loading persisted pipeline (if you want API in portfolio)

**Verification**

- Dashboard runs against SQL Server or cached parquet
- Manual test checklist in README

---

### Phase 7 — Testing, CI, GitHub polish

**Goals**

- pytest coverage for ingestion transforms, features, metrics utilities
- GitHub Actions: lint + unit tests (integration job optional with secrets)
- README: architecture diagram, setup, Kaggle download instructions, demo screenshots

**Verification**

- `pytest` passes locally
- Repository contains no raw Kaggle CSV

---

## 6. Open questions / blockers (Phase 2 inputs)

Please confirm before database work:

1. **SQL Server:** Is it installed locally? Instance name and auth mode?
2. **Database name** and whether you prefer a single denormalized table vs star schema lite.
3. **CSV location:** Keep at project root or relocate to `data/raw/` (recommend relocate via copy + `.gitignore`).
4. **Git:** Install Git for Windows and add to PATH for GitHub workflow?
5. **FastAPI:** Include in scope or Streamlit-only for portfolio?
6. **Excel file:** You mentioned Excel; only CSV was found — is another file expected?

---

## 7. Data governance

- **Do not commit** `WA_Fn-UseC_-Telco-Customer-Churn.csv` to GitHub.
- README will link to [Kaggle: Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) for acquisition steps.
- No PII beyond synthetic telco customer IDs; still treat as sample data only.

---

## 8. Success criteria (whole project)

| Criterion | Measure |
|-----------|---------|
| Data pipeline | CSV → SQL Server with documented QA |
| Analytics | SQL + Python EDA with aligned churn KPIs |
| ML | Holdout metrics reported without exaggeration |
| Explainability | SHAP + actionable recommendation fields |
| UX | Streamlit dashboard usable for demo |
| Engineering | Tests, docs, clean structure suitable for portfolio review |

---

*Phase 1 complete. Await your approval before Phase 2 implementation.*
