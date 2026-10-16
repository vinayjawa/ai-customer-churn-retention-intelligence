# Tests

Configuration: [pytest.ini](../pytest.ini) sets `pythonpath = src`.

## Run (safe default)

```powershell
python -m pytest -m "not integration" -v
```

These tests use synthetic data or local CSV validation and do **not** require SQL Server.

## Integration tests (optional — writes database)

```powershell
$env:CHURN_DB_INTEGRATION = "1"
python -m pytest -m integration -v
```

`tests/integration/test_db_ingestion.py` runs full ingestion and **appends a staging batch**.

## Layout

| Path | Focus |
|------|--------|
| [unit/test_csv_validation.py](unit/test_csv_validation.py) | Telco CSV rules |
| [unit/test_modeling.py](unit/test_modeling.py) | Features, split, metrics |
| [unit/test_analytics_eda.py](unit/test_analytics_eda.py) | Bands and segments |
| [unit/test_explain_retention_scoring.py](unit/test_explain_retention_scoring.py) | SHAP alignment, thresholds, rules |
| [unit/test_dashboard_data.py](unit/test_dashboard_data.py) | Latest score batch, KPIs, ID sanitization |
| [unit/test_phase7_regression.py](unit/test_phase7_regression.py) | Artifact presence and metric regression |
| [unit/test_config.py](unit/test_config.py) | Config without live DB |
