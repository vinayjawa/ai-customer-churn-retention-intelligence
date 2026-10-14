/*
  Post-load data-quality summary for analytics.customer.
*/
SELECT
    COUNT(*) AS customer_rows,
    SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_yes_rows,
    SUM(CASE WHEN total_charges_blank = 1 THEN 1 ELSE 0 END) AS blank_total_charges_rows,
    SUM(CASE WHEN total_charges_blank = 1 AND tenure <> 0 THEN 1 ELSE 0 END) AS blank_total_nonzero_tenure
FROM analytics.customer;

SELECT ingest_batch_id, reject_reason, COUNT(*) AS reject_count
FROM analytics.dq_load_reject
GROUP BY ingest_batch_id, reject_reason
ORDER BY reject_count DESC;
