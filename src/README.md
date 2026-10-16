# Python source (`src/`)

Install/run pattern:

```powershell
$env:PYTHONPATH = "src"
```

## Package: `churn_intel`

| Path | Role |
|------|------|
| [churn_intel/config.py](churn_intel/config.py) | Settings from `.env` |
| [churn_intel/db.py](churn_intel/db.py) | SQLAlchemy engine and SQL file execution |
| [churn_intel/connection_check.py](churn_intel/connection_check.py) | Connectivity CLI |
| [churn_intel/ingestion/](churn_intel/ingestion/) | CSV → SQL staging + analytics refresh |
| [churn_intel/quality/](churn_intel/quality/) | CSV validation |
| [churn_intel/analytics/](churn_intel/analytics/) | Python EDA from SQL mart |
| [churn_intel/modeling/](churn_intel/modeling/) | Baseline training and evaluation |
| [churn_intel/explain/](churn_intel/explain/) | SHAP explainability (`explain`, not `explainability`) |
| [churn_intel/scoring/](churn_intel/scoring/) | Batch prediction + SQL score store |
| [churn_intel/retention/](churn_intel/retention/) | High-risk segmentation and rules |
| [churn_intel/dashboard/](churn_intel/dashboard/) | Streamlit UI |

Module-level detail, commands, and side effects: **[../docs/PYTHON_GUIDE.md](../docs/PYTHON_GUIDE.md)**.
