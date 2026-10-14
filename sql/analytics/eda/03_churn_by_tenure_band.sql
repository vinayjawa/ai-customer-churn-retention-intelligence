/*
  Churn by tenure band (months):
    0-12, 13-24, 25-48, 49+
*/
SELECT
    tenure_band,
    customer_count,
    churn_count,
    churn_rate
FROM (
    SELECT
        CASE
            WHEN tenure BETWEEN 0 AND 12 THEN N'0-12 months'
            WHEN tenure BETWEEN 13 AND 24 THEN N'13-24 months'
            WHEN tenure BETWEEN 25 AND 48 THEN N'25-48 months'
            WHEN tenure >= 49 THEN N'49+ months'
            ELSE N'Unmapped'
        END AS tenure_band,
        CASE
            WHEN tenure BETWEEN 0 AND 12 THEN 1
            WHEN tenure BETWEEN 13 AND 24 THEN 2
            WHEN tenure BETWEEN 25 AND 48 THEN 3
            WHEN tenure >= 49 THEN 4
            ELSE 99
        END AS band_sort,
        COUNT(*) AS customer_count,
        SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
        CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
    FROM analytics.customer
    GROUP BY
        CASE
            WHEN tenure BETWEEN 0 AND 12 THEN N'0-12 months'
            WHEN tenure BETWEEN 13 AND 24 THEN N'13-24 months'
            WHEN tenure BETWEEN 25 AND 48 THEN N'25-48 months'
            WHEN tenure >= 49 THEN N'49+ months'
            ELSE N'Unmapped'
        END,
        CASE
            WHEN tenure BETWEEN 0 AND 12 THEN 1
            WHEN tenure BETWEEN 13 AND 24 THEN 2
            WHEN tenure BETWEEN 25 AND 48 THEN 3
            WHEN tenure >= 49 THEN 4
            ELSE 99
        END
) AS b
ORDER BY band_sort;
