/*
  Churn by contract type — analytics.customer
*/
SELECT
    Contract AS contract_type,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
FROM analytics.customer
GROUP BY Contract
ORDER BY churn_rate DESC, customer_count DESC;
