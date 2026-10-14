/*
  Analytics customer mart — typed, validated columns.

  Data-quality rules (documented):
  - customerID: required, unique primary key.
  - Churn: only Yes/No from source; stored as BIT (1=churned).
  - tenure, MonthlyCharges: must parse as numeric or row is rejected (logged in dq_load_reject).
  - TotalCharges: blank source string -> NULL (NOT zero). Numeric otherwise.
  - Blank TotalCharges with tenure <> 0 -> rejected.
  - SeniorCitizen: 0/1 only.
  - Categorical columns must match known IBM Telco domains or row is rejected.
*/
IF OBJECT_ID(N'analytics.dq_load_reject', N'U') IS NULL
BEGIN
    CREATE TABLE analytics.dq_load_reject (
        reject_id        BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ingest_batch_id  NVARCHAR(36)  NOT NULL,
        customerID       NVARCHAR(32)  NULL,
        reject_reason    NVARCHAR(500) NOT NULL,
        rejected_at_utc  DATETIME2(3)  NOT NULL CONSTRAINT DF_dq_load_reject_at DEFAULT (SYSUTCDATETIME())
    );
END;
GO

IF OBJECT_ID(N'analytics.customer', N'U') IS NULL
BEGIN
    CREATE TABLE analytics.customer (
        customerID           NVARCHAR(32)    NOT NULL,
        gender               NVARCHAR(10)    NOT NULL,
        SeniorCitizen        BIT             NOT NULL,
        Partner              NVARCHAR(5)     NOT NULL,
        Dependents           NVARCHAR(5)     NOT NULL,
        tenure               INT             NOT NULL,
        PhoneService         NVARCHAR(5)     NOT NULL,
        MultipleLines        NVARCHAR(32)    NOT NULL,
        InternetService      NVARCHAR(32)    NOT NULL,
        OnlineSecurity       NVARCHAR(32)    NOT NULL,
        OnlineBackup         NVARCHAR(32)    NOT NULL,
        DeviceProtection     NVARCHAR(32)    NOT NULL,
        TechSupport          NVARCHAR(32)    NOT NULL,
        StreamingTV          NVARCHAR(32)    NOT NULL,
        StreamingMovies      NVARCHAR(32)    NOT NULL,
        Contract             NVARCHAR(32)    NOT NULL,
        PaperlessBilling     NVARCHAR(5)     NOT NULL,
        PaymentMethod        NVARCHAR(64)    NOT NULL,
        MonthlyCharges       DECIMAL(10, 2)  NOT NULL,
        TotalCharges         DECIMAL(12, 2)  NULL,
        total_charges_blank  BIT             NOT NULL,
        Churn                BIT             NOT NULL,
        ingest_batch_id      NVARCHAR(36)    NOT NULL,
        loaded_at_utc        DATETIME2(3)    NOT NULL CONSTRAINT DF_analytics_customer_loaded DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT PK_analytics_customer PRIMARY KEY (customerID)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_analytics_customer_churn'
      AND object_id = OBJECT_ID(N'analytics.customer')
)
BEGIN
    CREATE INDEX IX_analytics_customer_churn ON analytics.customer (Churn);
END;
GO
