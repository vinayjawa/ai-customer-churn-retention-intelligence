# Troubleshooting

## PYTHONPATH / ModuleNotFoundError: churn_intel

Set before any module command:

```powershell
$env:PYTHONPATH = "src"
```

Or install the package in editable mode (only if you choose to):

```powershell
python -m pip install -e .
```

*(Editable install requires a packaging setup; the project standard is `PYTHONPATH=src`.)*

## ODBC / connection errors

| Symptom | Things to check |
|---------|-----------------|
| Driver not found | Install [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server); match `CHURN_ODBC_DRIVER` in `.env` |
| Certificate / encryption | Set `CHURN_TRUST_SERVER_CERTIFICATE=yes` for local dev with Driver 18 |
| Login failed | Windows auth: ensure your Windows user has access; SQL auth: set `CHURN_DB_AUTH=sql` and user/password |
| Cannot open database | Create `ChurnIntel` (or your `CHURN_DB_NAME`) on the server |
| Wrong instance | Use `SERVER\INSTANCE` in `CHURN_DB_SERVER`; backslashes are preserved in config (not URL-encoded incorrectly) |

Run:

```powershell
$env:PYTHONPATH = "src"
python -m churn_intel.connection_check
```

## Ingestion: ODBC parameter limit

Bulk insert uses chunked `to_sql` (2100 parameter limit). If you see ODBC parameter errors, reduce `CHURN_INGEST_BATCH_SIZE` in `.env`.

## Dashboard: “Unable to load customer data”

- SQL unreachable or empty `analytics.customer`.
- Run ingestion once (writes DB) or fix `.env`.

## Dashboard: score KPIs missing

- No rows in `ml.customer_churn_score` and no score CSV.
- Run `python -m churn_intel.scoring` (**appends SQL**) or ensure CSV exists.
- Toggle SQL off to test CSV fallback.

## Dashboard: wrong batch / duplicate customers in scores

Score table is append-only. Dashboard selects **max `scored_at_utc`**. If warnings appear, inspect batches:

```powershell
$env:PYTHONPATH = "src"
python scripts/inspect_scores.py
```

## Tests: integration skipped

Default pytest excludes integration. To run ( **appends staging** ):

```powershell
$env:CHURN_DB_INTEGRATION = "1"
python -m pytest -m integration -v
```

## Artifacts missing on Model / SHAP pages

Run prior phases without skipping:

- `python -m churn_intel.modeling`
- `python -m churn_intel.explain`

These overwrite local artifacts under `artifacts/`.

## Git / sharing

`.env`, raw CSV, processed data, and `artifacts/` are gitignored. For public repos, review [../data/README.md](../data/README.md) before publishing.
