/*
  Overall churn KPIs — source: analytics.customer
  Churn = 1 indicates churned (Yes); Churn = 0 retained (No).
*/
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churned_customers,
    SUM(CASE WHEN Churn = 0 THEN 1 ELSE 0 END) AS retained_customers,
    CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS overall_churn_rate,
    AVG(CAST(tenure AS DECIMAL(10, 2))) AS avg_tenure_months,
    MIN(MonthlyCharges) AS min_monthly_charges,
    MAX(MonthlyCharges) AS max_monthly_charges,
    AVG(MonthlyCharges) AS avg_monthly_charges,
    MIN(TotalCharges) AS min_total_charges_non_null,
    MAX(TotalCharges) AS max_total_charges_non_null,
    AVG(TotalCharges) AS avg_total_charges_non_null,
    SUM(CASE WHEN total_charges_blank = 1 THEN 1 ELSE 0 END) AS total_charges_blank_count
FROM analytics.customer;
