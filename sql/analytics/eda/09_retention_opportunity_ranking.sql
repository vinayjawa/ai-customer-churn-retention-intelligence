/*
  Retention opportunity ranking by segment.
  Minimum segment size: 30 customers (documented threshold).
  Ranked by churned customer count (volume impact), then churn rate.
*/
DECLARE @min_segment_size INT = 30;

WITH segments AS (
    SELECT
        N'Contract' AS segment_type,
        Contract AS segment_value,
        COUNT(*) AS customer_count,
        SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_count,
        CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6)) AS churn_rate
    FROM analytics.customer
    GROUP BY Contract

    UNION ALL

    SELECT
        N'PaymentMethod',
        PaymentMethod,
        COUNT(*),
        SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END),
        CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6))
    FROM analytics.customer
    GROUP BY PaymentMethod

    UNION ALL

    SELECT
        N'InternetService',
        InternetService,
        COUNT(*),
        SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END),
        CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6))
    FROM analytics.customer
    GROUP BY InternetService

    UNION ALL

    SELECT
        N'TenureBand',
        CASE
            WHEN tenure BETWEEN 0 AND 12 THEN N'0-12 months'
            WHEN tenure BETWEEN 13 AND 24 THEN N'13-24 months'
            WHEN tenure BETWEEN 25 AND 48 THEN N'25-48 months'
            WHEN tenure >= 49 THEN N'49+ months'
        END,
        COUNT(*),
        SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END),
        CAST(SUM(CASE WHEN Churn = 1 THEN 1.0 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(9, 6))
    FROM analytics.customer
    GROUP BY
        CASE
            WHEN tenure BETWEEN 0 AND 12 THEN N'0-12 months'
            WHEN tenure BETWEEN 13 AND 24 THEN N'13-24 months'
            WHEN tenure BETWEEN 25 AND 48 THEN N'25-48 months'
            WHEN tenure >= 49 THEN N'49+ months'
        END
)
SELECT
    segment_type,
    segment_value,
    customer_count,
    churn_count,
    churn_rate,
    @min_segment_size AS min_segment_size_applied
FROM segments
WHERE customer_count >= @min_segment_size
ORDER BY churn_count DESC, churn_rate DESC, customer_count DESC;
