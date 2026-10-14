/*
  Churn by monthly charges band (USD):
    Under 35, 35-49.99, 50-69.99, 70-89.99, 90+
*/
SELECT
    charge_band,
    customer_count,
    churn_count,
    churn_rate
FROM (
    SELECT
        CASE
            WHEN MonthlyCharges < 35 THEN N'Under 35'
            WHEN MonthlyCharges >= 35 AND MonthlyCharges < 50 THEN N'35-49.99'
            WHEN MonthlyCharges >= 50 AND MonthlyCharges < 70 THEN N'50-69.99'
            WHEN MonthlyCharges >= 70 AND MonthlyCharges < 90 THEN N'70-89.99'
            WHEN MonthlyCharges >= 90 THEN N'90+'
            ELSE N'Unmapped'
        END AS charge_band,
        CASE
            WHEN MonthlyCharges < 35 THEN 1
            WHEN MonthlyCharges >= 35 AND MonthlyCharges < 50 THEN 2
            WHEN MonthlyCharges >= 50 AND MonthlyCharges < 70 THEN 3
            WHEN MonthlyCharges >= 70 AND MonthlyCharges < 90 THEN 4
            WHEN MonthlyCharges >= 90 THEN 5
            ELSE 99
        END AS band_sort,
        COUNT(*) AS customer_count,
        SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
        CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
    FROM analytics.customer
    GROUP BY
        CASE
            WHEN MonthlyCharges < 35 THEN N'Under 35'
            WHEN MonthlyCharges >= 35 AND MonthlyCharges < 50 THEN N'35-49.99'
            WHEN MonthlyCharges >= 50 AND MonthlyCharges < 70 THEN N'50-69.99'
            WHEN MonthlyCharges >= 70 AND MonthlyCharges < 90 THEN N'70-89.99'
            WHEN MonthlyCharges >= 90 THEN N'90+'
            ELSE N'Unmapped'
        END,
        CASE
            WHEN MonthlyCharges < 35 THEN 1
            WHEN MonthlyCharges >= 35 AND MonthlyCharges < 50 THEN 2
            WHEN MonthlyCharges >= 50 AND MonthlyCharges < 70 THEN 3
            WHEN MonthlyCharges >= 70 AND MonthlyCharges < 90 THEN 4
            WHEN MonthlyCharges >= 90 THEN 5
            ELSE 99
        END
) AS b
ORDER BY band_sort;
