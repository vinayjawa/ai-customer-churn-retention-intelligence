/*
  Demographic and account segments (descriptive; not causal).
*/
SELECT N'SeniorCitizen' AS dimension, CASE WHEN SeniorCitizen = 1 THEN N'Yes' ELSE N'No' END AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY SeniorCitizen;

SELECT N'Partner' AS dimension, Partner AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY Partner;

SELECT N'Dependents' AS dimension, Dependents AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY Dependents;

SELECT N'PaperlessBilling' AS dimension, PaperlessBilling AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY PaperlessBilling;

SELECT N'gender' AS dimension, gender AS category,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY gender;
