/*
  Create logical schemas (idempotent).
  Database: ChurnIntel (must exist before running scripts).
*/
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'stg')
    EXEC(N'CREATE SCHEMA stg AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'analytics')
    EXEC(N'CREATE SCHEMA analytics AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'ml')
    EXEC(N'CREATE SCHEMA ml AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'retention')
    EXEC(N'CREATE SCHEMA retention AUTHORIZATION dbo;');
GO
