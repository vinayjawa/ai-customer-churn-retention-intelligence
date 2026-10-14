from __future__ import annotations

import pytest

from churn_intel.config import get_settings
from churn_intel.ingestion.pipeline import run_ingestion


@pytest.mark.integration
def test_full_ingestion_against_sql_server(telco_csv_path) -> None:
    settings = get_settings()
    if not settings.db_integration:
        pytest.skip("Set CHURN_DB_INTEGRATION=1 to run SQL Server integration tests.")
    if not settings.is_db_configured():
        pytest.skip("Database environment variables are not configured.")

    result = run_ingestion(csv_path=telco_csv_path)
    assert result.validation.passed
    assert not result.errors, result.errors
    assert result.staging_rows_inserted == result.validation.row_count
    assert result.analytics_rows == result.validation.row_count
