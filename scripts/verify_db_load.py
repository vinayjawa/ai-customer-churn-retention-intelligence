"""Read-only post-ingestion verification (run with PYTHONPATH=src)."""

from __future__ import annotations

from sqlalchemy import text

from churn_intel.db import create_db_engine


def main() -> None:
    engine = create_db_engine()
    statements = [
        (
            "latest_batch",
            """
            SELECT TOP 1 ingest_batch_id, COUNT(*) AS stg_rows, MAX(ingested_at_utc) AS ingested_at_utc
            FROM stg.telco_customer_churn
            GROUP BY ingest_batch_id
            ORDER BY MAX(ingested_at_utc) DESC
            """,
        ),
        (
            "stg_totals",
            """
            SELECT COUNT(*) AS all_stg_rows, COUNT(DISTINCT ingest_batch_id) AS batch_count
            FROM stg.telco_customer_churn
            """,
        ),
        (
            "analytics_counts",
            """
            SELECT COUNT(*) AS total_rows, COUNT(DISTINCT customerID) AS distinct_ids,
              SUM(CASE WHEN Churn = 1 THEN 1 ELSE 0 END) AS churn_yes,
              SUM(CASE WHEN Churn = 0 THEN 1 ELSE 0 END) AS churn_no,
              SUM(CASE WHEN total_charges_blank = 1 THEN 1 ELSE 0 END) AS blank_total,
              SUM(CASE WHEN TotalCharges IS NULL THEN 1 ELSE 0 END) AS null_total_charges
            FROM analytics.customer
            """,
        ),
        (
            "dup_ids",
            """
            SELECT COUNT(*) AS dup_groups FROM (
              SELECT customerID FROM analytics.customer GROUP BY customerID HAVING COUNT(*) > 1
            ) d
            """,
        ),
        (
            "rejects",
            "SELECT COUNT(*) AS reject_rows FROM analytics.dq_load_reject",
        ),
        (
            "schemas",
            """
            SELECT name FROM sys.schemas
            WHERE name IN (N'stg', N'analytics', N'ml', N'retention')
            ORDER BY name
            """,
        ),
        (
            "objects",
            """
            SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA IN (N'stg', N'analytics', N'ml', N'retention')
            ORDER BY 1, 2
            """,
        ),
    ]
    with engine.connect() as conn:
        for label, sql in statements:
            rows = conn.execute(text(sql)).fetchall()
            print(f"--- {label} ---")
            for row in rows:
                print(tuple(row))
    engine.dispose()


if __name__ == "__main__":
    main()
