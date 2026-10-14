/*
  Refresh analytics.customer from a single staging batch.
  Placeholder :batch_id is replaced by Python before execution.
  Invalid rows are inserted into analytics.dq_load_reject (not silently dropped).
*/
DECLARE @batch_id NVARCHAR(36) = N'__BATCH_ID__';

DELETE FROM analytics.dq_load_reject WHERE ingest_batch_id = @batch_id;

INSERT INTO analytics.dq_load_reject (ingest_batch_id, customerID, reject_reason)
SELECT @batch_id, s.customerID, v.reject_reason
FROM stg.telco_customer_churn AS s
CROSS APPLY (
    SELECT reject_reason = CASE
        WHEN NULLIF(LTRIM(RTRIM(s.customerID)), N'') IS NULL THEN N'Missing customerID'
        WHEN LTRIM(RTRIM(s.Churn)) NOT IN (N'Yes', N'No') THEN N'Invalid Churn label'
        WHEN TRY_CONVERT(INT, s.tenure) IS NULL THEN N'Invalid tenure'
        WHEN TRY_CONVERT(DECIMAL(10, 2), s.MonthlyCharges) IS NULL THEN N'Invalid MonthlyCharges'
        WHEN LTRIM(RTRIM(s.SeniorCitizen)) NOT IN (N'0', N'1') THEN N'Invalid SeniorCitizen'
        WHEN LTRIM(RTRIM(s.gender)) NOT IN (N'Female', N'Male') THEN N'Invalid gender'
        WHEN LTRIM(RTRIM(s.Partner)) NOT IN (N'No', N'Yes') THEN N'Invalid Partner'
        WHEN LTRIM(RTRIM(s.Dependents)) NOT IN (N'No', N'Yes') THEN N'Invalid Dependents'
        WHEN LTRIM(RTRIM(s.PhoneService)) NOT IN (N'No', N'Yes') THEN N'Invalid PhoneService'
        WHEN LTRIM(RTRIM(s.MultipleLines)) NOT IN (N'No', N'No phone service', N'Yes') THEN N'Invalid MultipleLines'
        WHEN LTRIM(RTRIM(s.InternetService)) NOT IN (N'DSL', N'Fiber optic', N'No') THEN N'Invalid InternetService'
        WHEN LTRIM(RTRIM(s.OnlineSecurity)) NOT IN (N'No', N'No internet service', N'Yes') THEN N'Invalid OnlineSecurity'
        WHEN LTRIM(RTRIM(s.OnlineBackup)) NOT IN (N'No', N'No internet service', N'Yes') THEN N'Invalid OnlineBackup'
        WHEN LTRIM(RTRIM(s.DeviceProtection)) NOT IN (N'No', N'No internet service', N'Yes') THEN N'Invalid DeviceProtection'
        WHEN LTRIM(RTRIM(s.TechSupport)) NOT IN (N'No', N'No internet service', N'Yes') THEN N'Invalid TechSupport'
        WHEN LTRIM(RTRIM(s.StreamingTV)) NOT IN (N'No', N'No internet service', N'Yes') THEN N'Invalid StreamingTV'
        WHEN LTRIM(RTRIM(s.StreamingMovies)) NOT IN (N'No', N'No internet service', N'Yes') THEN N'Invalid StreamingMovies'
        WHEN LTRIM(RTRIM(s.Contract)) NOT IN (N'Month-to-month', N'One year', N'Two year') THEN N'Invalid Contract'
        WHEN LTRIM(RTRIM(s.PaperlessBilling)) NOT IN (N'No', N'Yes') THEN N'Invalid PaperlessBilling'
        WHEN LTRIM(RTRIM(s.PaymentMethod)) NOT IN (
            N'Bank transfer (automatic)', N'Credit card (automatic)', N'Electronic check', N'Mailed check'
        ) THEN N'Invalid PaymentMethod'
        WHEN LTRIM(RTRIM(s.TotalCharges)) = N''
             AND TRY_CONVERT(INT, s.tenure) <> 0 THEN N'Blank TotalCharges with non-zero tenure'
        WHEN LTRIM(RTRIM(s.TotalCharges)) <> N''
             AND TRY_CONVERT(DECIMAL(12, 2), s.TotalCharges) IS NULL THEN N'Invalid TotalCharges'
        ELSE NULL
    END
) AS v
WHERE s.ingest_batch_id = @batch_id
  AND v.reject_reason IS NOT NULL;

DELETE FROM analytics.customer;

INSERT INTO analytics.customer (
    customerID, gender, SeniorCitizen, Partner, Dependents, tenure,
    PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup,
    DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract,
    PaperlessBilling, PaymentMethod, MonthlyCharges, TotalCharges, total_charges_blank,
    Churn, ingest_batch_id
)
SELECT
    s.customerID,
    s.gender,
    CASE WHEN LTRIM(RTRIM(s.SeniorCitizen)) = N'1' THEN 1 ELSE 0 END,
    s.Partner,
    s.Dependents,
    TRY_CONVERT(INT, s.tenure),
    s.PhoneService,
    s.MultipleLines,
    s.InternetService,
    s.OnlineSecurity,
    s.OnlineBackup,
    s.DeviceProtection,
    s.TechSupport,
    s.StreamingTV,
    s.StreamingMovies,
    s.Contract,
    s.PaperlessBilling,
    s.PaymentMethod,
    TRY_CONVERT(DECIMAL(10, 2), s.MonthlyCharges),
    CASE
        WHEN LTRIM(RTRIM(s.TotalCharges)) = N'' THEN NULL
        ELSE TRY_CONVERT(DECIMAL(12, 2), s.TotalCharges)
    END,
    CASE WHEN LTRIM(RTRIM(s.TotalCharges)) = N'' THEN 1 ELSE 0 END,
    CASE WHEN LTRIM(RTRIM(s.Churn)) = N'Yes' THEN 1 ELSE 0 END,
    s.ingest_batch_id
FROM stg.telco_customer_churn AS s
WHERE s.ingest_batch_id = @batch_id
  AND NOT EXISTS (
      SELECT 1
      FROM analytics.dq_load_reject AS r
      WHERE r.ingest_batch_id = @batch_id
        AND r.customerID = s.customerID
  );
GO
