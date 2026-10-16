# Setup guide

For someone opening this project for the first time on Windows (Linux/macOS steps are similar with path adjustments).

## 1. Prerequisites

| Software | Notes |
|----------|--------|
| Python | **3.11+** tested with **3.14**; see `requirements.txt` |
| Microsoft SQL Server | Local or accessible instance |
| ODBC Driver 18 for SQL Server | Or 17; `connection_check` detects drivers |
| Git (optional) | For version control only — not required to run the app |

## 2. Get the dataset

1. Download [Telco Customer Churn on Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) (license applies).
2. Place the file at:

   `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`

3. Do **not** commit the CSV or upload it to public repos.

## 3. Python environment

```powershell
cd <project-root>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> **Note:** Installing packages modifies your local environment only. Skip or adjust versions only with intent — the project pins major ranges in `requirements.txt`.

## 4. Configure environment variables

```powershell
copy .env.example .env
```

Edit `.env` locally (never commit):

| Variable | Example placeholder | Purpose |
|----------|---------------------|---------|
| `CHURN_DB_SERVER` | `localhost\SQLEXPRESS` or `myserver,1433` | SQL Server host |
| `CHURN_DB_NAME` | `ChurnIntel` | Database name |
| `CHURN_DB_AUTH` | `windows` or `sql` | Authentication mode |
| `CHURN_DB_USER` / `CHURN_DB_PASSWORD` | Only for SQL auth | Leave empty for Windows auth |
| `CHURN_ODBC_DRIVER` | `ODBC Driver 18 for SQL Server` | Must match installed driver |
| `CHURN_TRUST_SERVER_CERTIFICATE` | `yes` | Common for local Driver 18 |
| `CHURN_CSV_PATH` | `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` | Ingestion default |

Optional: `CHURN_DATABASE_URL` overrides individual fields.

## 5. Create the database (once)

In SSMS or `sqlcmd`:

```sql
CREATE DATABASE ChurnIntel;
```

Use the same name as `CHURN_DB_NAME`.

## 6. DDL — create schemas and tables

**Option A (recommended):** let ingestion apply DDL 01–06:

```powershell
$env:PYTHONPATH = "src"
python -m churn_intel.ingestion
```

**Warning:** This also **loads data** and **replaces** `analytics.customer`.

**Option B:** run `sql/ddl/01_schemas.sql` through `06_analytics_views.sql` manually in SSMS, then ingestion with `--skip-ddl` if objects already exist.

**Scoring columns (07):** applied automatically on first `python -m churn_intel.scoring` run.

## 7. Verify connectivity

```powershell
$env:PYTHONPATH = "src"
python -m churn_intel.connection_check
```

Expect success message and row-count query against configured database. Fix ODBC/auth using [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## 8. End-to-end pipeline (optional, writes data/files)

Run only when you intend to refresh data and artifacts.

| Action | Command | Side effects |
|--------|---------|--------------|
| Ingest | `python -m churn_intel.ingestion` | Staging append; analytics mart replace |
| SQL EDA CSVs | `python scripts/run_sql_eda.py` | Writes `data/processed/sql_eda/` |
| Python EDA | `python -m churn_intel.analytics` | Writes `artifacts/eda/`, processed CSVs |
| Train | `python -m churn_intel.modeling` | Overwrites model + evaluation artifacts |
| SHAP | `python -m churn_intel.explain` | Overwrites explainability outputs |
| Score | `python -m churn_intel.scoring` | **Appends** SQL scores; writes score CSV |
| Retention | `python -m churn_intel.retention` | Overwrites retention CSVs |

Use `python -m churn_intel.scoring --no-sql` to write CSV only (no SQL append).

## 9. Launch Streamlit dashboard

```powershell
$env:PYTHONPATH = "src"
python -m streamlit run src/churn_intel/dashboard/app.py
```

- Open the URL shown (typically `http://localhost:8501`).
- Stop with **Ctrl+C** in the terminal.

## 10. Confirm SQL vs CSV score source

1. Open dashboard sidebar.
2. Ensure **“Load scores from SQL Server”** is **on**.
3. On **Executive Overview**, check the info box: `Latest score snapshot` should show source **`sql_server`**.
4. Turn the toggle **off** only if SQL is unavailable — source becomes **`csv_fallback`** when `data/processed/retention/customer_churn_scores.csv` exists.

Customer data always requires SQL (`analytics.customer`).

## 11. Tests

Safe default (no live DB ingestion):

```powershell
python -m pytest -m "not integration" -v
```

Integration tests require `CHURN_DB_INTEGRATION=1` and **append a staging batch**.

## 12. What stays private

- `.env`
- `data/raw/`, `data/processed/`
- `artifacts/` (models may embed training patterns)
- Root copy `WA_Fn-UseC_-Telco-Customer-Churn.csv` if present (also in `.gitignore`)

See root `.gitignore` and [../data/README.md](../data/README.md).
