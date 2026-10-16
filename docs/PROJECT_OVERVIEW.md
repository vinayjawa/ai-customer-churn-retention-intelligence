# Project overview

## What this project is

An end-to-end **portfolio demonstration** of customer churn analytics for a telco-style dataset: validate and load data into **SQL Server**, explore churn with **SQL and Python**, train **baseline classifiers**, explain the selected model with **SHAP**, score customers, apply **retention prioritization rules**, and present results in a **Streamlit** dashboard.

It is **not** a production system. There is no live deployment, SLA, or proven business ROI.

## Business problem

Subscription businesses lose revenue when customers cancel. Teams need a repeatable way to:

- Understand **who churned historically** and in which segments.
- Estimate **churn risk** for the current customer base.
- Explain **which factors align with higher risk** (association, not causation).
- Prioritize **retention outreach** with transparent rules.

## Business objectives (implemented)

| Objective | How the project addresses it |
|-----------|------------------------------|
| Trusted customer mart | `analytics.customer` built from validated CSV via staging |
| Segment insights | SQL EDA scripts + Python EDA plots/CSVs |
| Predictive baseline | Three models compared; logistic regression selected by test PR-AUC |
| Explainability | Global SHAP for the selected linear model |
| Operational scoring | Batch scores to SQL (`ml.customer_churn_score`) and CSV |
| Retention intelligence | 75th-percentile high-risk flag + rule-based recommendations |
| Stakeholder demo | Six-page Streamlit dashboard (read-only) |

## Dataset

IBM Telco Customer Churn (public Kaggle sample). **You must download it yourself**; it is not redistributed in this repository. See [DATASET_PROFILE.md](DATASET_PROFILE.md) and [SETUP_GUIDE.md](SETUP_GUIDE.md).

Reference row counts in saved model metadata: **7,043** customers; **~26.5%** churn prevalence on the training snapshot.

## What to run first

1. [SETUP_GUIDE.md](SETUP_GUIDE.md) — environment and database
2. `python -m churn_intel.connection_check` — connectivity
3. Optional full pipeline (writes DB/files) — see command table in SETUP_GUIDE
4. Streamlit dashboard — [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)

## Where code lives

| Concern | Location |
|---------|----------|
| SQL DDL/DML/EDA | [../sql/README.md](../sql/README.md) |
| Python package | `src/churn_intel/` — [../src/README.md](../src/README.md) |
| Tests | [../tests/README.md](../tests/README.md) |
| Generated outputs | [../artifacts/README.md](../artifacts/README.md), `data/processed/` |
