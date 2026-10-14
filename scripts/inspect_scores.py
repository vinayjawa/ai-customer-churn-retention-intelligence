from sqlalchemy import text
from churn_intel.db import create_db_engine

e = create_db_engine()
with e.connect() as c:
    cols = c.execute(
        text(
            "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA='ml' AND TABLE_NAME='customer_churn_score' ORDER BY ORDINAL_POSITION"
        )
    ).fetchall()
    print("columns", cols)
    stats = c.execute(
        text(
            "SELECT COUNT(*) total, COUNT(DISTINCT customerID) dc, COUNT(DISTINCT scored_at_utc) dts "
            "FROM ml.customer_churn_score"
        )
    ).one()
    print("stats", stats)
    batch = c.execute(
        text(
            "SELECT scored_at_utc, model_version, COUNT(*) cnt FROM ml.customer_churn_score "
            "GROUP BY scored_at_utc, model_version ORDER BY scored_at_utc DESC"
        )
    ).fetchall()
    print("batches", batch)
e.dispose()
