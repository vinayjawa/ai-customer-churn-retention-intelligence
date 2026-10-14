/*
  Churn by internet service and add-on services.
  Values such as 'No internet service' are distinct categories (not treated as NULL).
*/

-- Internet service
SELECT
    N'InternetService' AS dimension,
    InternetService AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY InternetService;

-- Online security
SELECT
    N'OnlineSecurity' AS dimension,
    OnlineSecurity AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY OnlineSecurity;

-- Tech support
SELECT
    N'TechSupport' AS dimension,
    TechSupport AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY TechSupport;

-- Online backup
SELECT
    N'OnlineBackup' AS dimension,
    OnlineBackup AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY OnlineBackup;

-- Device protection
SELECT
    N'DeviceProtection' AS dimension,
    DeviceProtection AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY DeviceProtection;
