"""CSV ingestion into SQL Server staging and analytics refresh."""

from churn_intel.ingestion.pipeline import IngestionResult, run_ingestion

__all__ = ["IngestionResult", "run_ingestion"]
