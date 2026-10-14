CREATE OR ALTER VIEW analytics.v_customer_churn
AS
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
    CASE WHEN Churn = 1 THEN N'Yes' ELSE N'No' END AS ChurnLabel,
    Churn AS ChurnBit,
    ingest_batch_id,
    loaded_at_utc
FROM analytics.customer;
GO
