# SQL scripts

Microsoft SQL Server scripts for the **ChurnIntel** database.

## Layout

| Folder / file | Contents |
|---------------|----------|
| [ddl/](ddl/) | Idempotent schema and table creation (run order **01 → 06**) |
| [ddl/07_ml_scoring_columns.sql](ddl/07_ml_scoring_columns.sql) | Optional column additions for scoring (also run from Python scoring) |
| [dml/](dml/) | `01_refresh_analytics_from_stg.sql` — rebuilds `analytics.customer` from one staging batch |
| [analytics/](analytics/) | DQ summary, view script, and [eda/](analytics/eda/) analytical queries |

## Documentation

Full inventory, execution order, and read vs write classification: **[../docs/SQL_GUIDE.md](../docs/SQL_GUIDE.md)**.

## Typical usage

- **Automated:** `python -m churn_intel.ingestion` applies DDL 01–06 (unless `--skip-ddl`) and runs DML refresh.
- **Analytical:** `python scripts/run_sql_eda.py` runs EDA SELECTs and exports CSVs (read-only on the database).

Do not run DML manually unless you substitute a valid `ingest_batch_id`.
