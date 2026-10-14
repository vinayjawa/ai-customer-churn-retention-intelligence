/*
  Reserved for Phase 4+ model scoring and metadata.
*/
IF OBJECT_ID(N'ml.model_registry', N'U') IS NULL
BEGIN
    CREATE TABLE ml.model_registry (
        model_id          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        model_name        NVARCHAR(128)     NOT NULL,
        model_version     NVARCHAR(64)      NOT NULL,
        trained_at_utc    DATETIME2(3)      NULL,
        artifact_path     NVARCHAR(500)     NULL,
        notes             NVARCHAR(1000)    NULL,
        created_at_utc    DATETIME2(3)      NOT NULL CONSTRAINT DF_ml_model_registry_created DEFAULT (SYSUTCDATETIME())
    );
END;
GO

IF OBJECT_ID(N'ml.customer_churn_score', N'U') IS NULL
BEGIN
    CREATE TABLE ml.customer_churn_score (
        score_id          BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customerID        NVARCHAR(32)         NOT NULL,
        model_id          INT                  NOT NULL,
        churn_probability DECIMAL(9, 6)        NOT NULL,
        scored_at_utc     DATETIME2(3)         NOT NULL CONSTRAINT DF_ml_customer_churn_score_at DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_ml_score_model FOREIGN KEY (model_id) REFERENCES ml.model_registry (model_id)
    );
END;
GO
