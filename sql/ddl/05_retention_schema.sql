/*
  Reserved for Phase 5+ retention recommendations and campaign tracking.
*/
IF OBJECT_ID(N'retention.recommendation', N'U') IS NULL
BEGIN
    CREATE TABLE retention.recommendation (
        recommendation_id   BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customerID          NVARCHAR(32)         NOT NULL,
        recommendation_code NVARCHAR(64)         NOT NULL,
        recommendation_text NVARCHAR(1000)       NOT NULL,
        created_at_utc      DATETIME2(3)         NOT NULL CONSTRAINT DF_retention_recommendation_created DEFAULT (SYSUTCDATETIME())
    );
END;
GO

IF OBJECT_ID(N'retention.campaign_touch', N'U') IS NULL
BEGIN
    CREATE TABLE retention.campaign_touch (
        touch_id            BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        customerID          NVARCHAR(32)         NOT NULL,
        channel             NVARCHAR(64)         NOT NULL,
        outcome             NVARCHAR(64)         NULL,
        touched_at_utc      DATETIME2(3)         NOT NULL CONSTRAINT DF_retention_campaign_touch_at DEFAULT (SYSUTCDATETIME())
    );
END;
GO
