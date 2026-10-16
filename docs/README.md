# Documentation index

Start here after reading the [root README](../README.md).

| Document | Audience | Contents |
|----------|----------|----------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Recruiters, hiring managers | Problem, objectives, features, honest scope |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Developers, architects | Data flow, schemas, file vs SQL sources |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | New contributors | Install, `.env`, DDL, commands, side effects |
| [SQL_GUIDE.md](SQL_GUIDE.md) | SQL developers | Every SQL script, order, read vs write |
| [PYTHON_GUIDE.md](PYTHON_GUIDE.md) | Python developers | Modules, CLI entry points, I/O |
| [MODEL_DOCUMENTATION.md](MODEL_DOCUMENTATION.md) | Data scientists | Target, features, metrics, thresholds |
| [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) | BI / analytics | Pages, KPIs, filters, fallbacks |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Everyone | ODBC, auth, PYTHONPATH, common errors |

## Phase reports (historical detail)

These predate the consolidated guides but remain accurate references:

- [DATASET_PROFILE.md](DATASET_PROFILE.md) — column-level profile
- [EDA_BUSINESS_INSIGHTS.md](EDA_BUSINESS_INSIGHTS.md) — SQL-backed segment findings
- [BASELINE_MODEL_REPORT.md](BASELINE_MODEL_REPORT.md) — modeling phase report
- [SHAP_EXPLAINABILITY_REPORT.md](SHAP_EXPLAINABILITY_REPORT.md) — global SHAP run
- [RETENTION_INTELLIGENCE.md](RETENTION_INTELLIGENCE.md) — high-risk rules and outputs
- [STREAMLIT_DASHBOARD.md](STREAMLIT_DASHBOARD.md) — short dashboard notes (see also DASHBOARD_GUIDE)
- [PROJECT_PLAN.md](PROJECT_PLAN.md) — original build plan

## Screenshots

Streamlit page PNGs: [screenshots/README.md](screenshots/README.md). EDA and SHAP batch plots live under `artifacts/` after you run analytics and explainability (gitignored).
