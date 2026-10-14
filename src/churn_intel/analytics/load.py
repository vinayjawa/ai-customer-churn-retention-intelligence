"""Load analytics.customer from SQL Server."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from churn_intel.db import create_db_engine

CUSTOMER_QUERY = text(
    """
    SELECT
        customerID,
        gender,
        SeniorCitizen,
        Partner,
        Dependents,
        tenure,
        PhoneService,
        MultipleLines,
        InternetService,
        OnlineSecurity,
        OnlineBackup,
        DeviceProtection,
        TechSupport,
        StreamingTV,
        StreamingMovies,
        Contract,
        PaperlessBilling,
        PaymentMethod,
        MonthlyCharges,
        TotalCharges,
        total_charges_blank,
        Churn,
        ingest_batch_id,
        loaded_at_utc
    FROM analytics.customer
    """
)


def load_customer_mart() -> pd.DataFrame:
    """
    Read typed customer mart from SQL Server.
    - Churn remains BIT-like (0/1) for modeling prep; use ChurnLabel for reporting.
    - TotalCharges NULL preserved when total_charges_blank=1 (not filled with zero).
    """
    engine = create_db_engine()
    try:
        df = pd.read_sql(CUSTOMER_QUERY, engine)
    finally:
        engine.dispose()

    df["Churn"] = df["Churn"].astype(int)
    df["SeniorCitizen"] = df["SeniorCitizen"].astype(int)
    df["total_charges_blank"] = df["total_charges_blank"].astype(int)
    df["ChurnLabel"] = df["Churn"].map({1: "Yes", 0: "No"})
    df["MonthlyCharges"] = pd.to_numeric(df["MonthlyCharges"], errors="coerce")
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce").astype("Int64")
    return df
