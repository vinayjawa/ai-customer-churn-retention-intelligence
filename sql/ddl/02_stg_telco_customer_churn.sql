/*
  Staging: auditable copy of source CSV values.
  TotalCharges retained as text to preserve blank strings from source.
*/
IF OBJECT_ID(N'stg.telco_customer_churn', N'U') IS NULL
BEGIN
    CREATE TABLE stg.telco_customer_churn (
        customerID           NVARCHAR(32)   NOT NULL,
        gender               NVARCHAR(10)   NOT NULL,
        SeniorCitizen        NVARCHAR(5)    NOT NULL,
        Partner              NVARCHAR(5)    NOT NULL,
        Dependents           NVARCHAR(5)    NOT NULL,
        tenure               NVARCHAR(10)   NOT NULL,
        PhoneService         NVARCHAR(5)    NOT NULL,
        MultipleLines        NVARCHAR(32)   NOT NULL,
        InternetService      NVARCHAR(32)   NOT NULL,
        OnlineSecurity       NVARCHAR(32)   NOT NULL,
        OnlineBackup         NVARCHAR(32)   NOT NULL,
        DeviceProtection     NVARCHAR(32)   NOT NULL,
        TechSupport          NVARCHAR(32)   NOT NULL,
        StreamingTV          NVARCHAR(32)   NOT NULL,
        StreamingMovies      NVARCHAR(32)   NOT NULL,
        Contract             NVARCHAR(32)   NOT NULL,
        PaperlessBilling     NVARCHAR(5)    NOT NULL,
        PaymentMethod        NVARCHAR(64)   NOT NULL,
        MonthlyCharges       NVARCHAR(32)   NOT NULL,
        TotalCharges         NVARCHAR(32)   NOT NULL,
        Churn                NVARCHAR(5)    NOT NULL,
        ingest_batch_id      NVARCHAR(36)   NOT NULL,
        ingested_at_utc      DATETIME2(3)   NOT NULL,
        source_file          NVARCHAR(260)  NOT NULL,
        CONSTRAINT PK_stg_telco_customer_churn PRIMARY KEY (customerID, ingest_batch_id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_stg_telco_customer_churn_batch'
      AND object_id = OBJECT_ID(N'stg.telco_customer_churn')
)
BEGIN
    CREATE INDEX IX_stg_telco_customer_churn_batch
        ON stg.telco_customer_churn (ingest_batch_id, ingested_at_utc DESC);
END;
GO
