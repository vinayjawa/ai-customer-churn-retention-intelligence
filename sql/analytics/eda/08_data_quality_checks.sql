/*
  Data quality checks on analytics.customer (read-only).
*/
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT customerID) AS distinct_customer_ids,
    COUNT(*) - COUNT(DISTINCT customerID) AS duplicate_id_rows
FROM analytics.customer;

SELECT
    SUM(CASE WHEN customerID IS NULL OR LTRIM(RTRIM(customerID)) = N'' THEN 1 ELSE 0 END) AS missing_customer_id,
    SUM(CASE WHEN MonthlyCharges IS NULL THEN 1 ELSE 0 END) AS null_monthly_charges,
    SUM(CASE WHEN tenure IS NULL THEN 1 ELSE 0 END) AS null_tenure,
    SUM(CASE WHEN TotalCharges IS NULL THEN 1 ELSE 0 END) AS null_total_charges,
    SUM(CASE WHEN total_charges_blank = 1 THEN 1 ELSE 0 END) AS total_charges_blank_flag,
    SUM(CASE WHEN total_charges_blank = 1 AND tenure <> 0 THEN 1 ELSE 0 END) AS blank_total_nonzero_tenure
FROM analytics.customer;

SELECT COUNT(*) AS reject_rows_in_dq_table FROM analytics.dq_load_reject;
