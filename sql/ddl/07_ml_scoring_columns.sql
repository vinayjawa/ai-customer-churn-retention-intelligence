/*
  Extend ml.customer_churn_score for Phase 5 (idempotent, non-destructive).
  Preserves existing rows; adds predicted label if missing.
*/
IF OBJECT_ID(N'ml.customer_churn_score', N'U') IS NOT NULL
AND NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'ml.customer_churn_score')
      AND name = N'predicted_churn'
)
BEGIN
    ALTER TABLE ml.customer_churn_score
        ADD predicted_churn BIT NOT NULL
            CONSTRAINT DF_ml_customer_churn_score_predicted DEFAULT (0);
END;
GO

IF OBJECT_ID(N'ml.customer_churn_score', N'U') IS NOT NULL
AND NOT EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'ml.customer_churn_score')
      AND name = N'model_version'
)
BEGIN
    ALTER TABLE ml.customer_churn_score
        ADD model_version NVARCHAR(64) NULL;
END;
GO
