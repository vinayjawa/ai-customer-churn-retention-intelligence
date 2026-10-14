"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, quote_plus

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key, default)
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


@dataclass(frozen=True)
class Settings:
    """Runtime settings for database and ingestion."""

    db_server: str | None
    db_name: str
    db_auth: str
    db_user: str | None
    db_password: str | None
    odbc_driver: str
    trust_server_certificate: bool
    database_url_override: str | None
    csv_path: Path
    ingest_batch_size: int
    db_integration: bool

    @classmethod
    def from_env(cls) -> Settings:
        auth = (_env("CHURN_DB_AUTH", "windows") or "windows").lower()
        trust_raw = (_env("CHURN_TRUST_SERVER_CERTIFICATE", "yes") or "yes").lower()
        csv_rel = _env("CHURN_CSV_PATH", "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")
        batch_raw = _env("CHURN_INGEST_BATCH_SIZE", "500") or "500"
        integration_raw = (_env("CHURN_DB_INTEGRATION", "0") or "0").lower()

        return cls(
            db_server=_env("CHURN_DB_SERVER"),
            db_name=_env("CHURN_DB_NAME", "ChurnIntel") or "ChurnIntel",
            db_auth=auth,
            db_user=_env("CHURN_DB_USER"),
            db_password=_env("CHURN_DB_PASSWORD"),
            odbc_driver=_env("CHURN_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
            or "ODBC Driver 18 for SQL Server",
            trust_server_certificate=trust_raw in ("1", "true", "yes", "y"),
            database_url_override=_env("CHURN_DATABASE_URL"),
            csv_path=PROJECT_ROOT / csv_rel,
            ingest_batch_size=max(1, int(batch_raw)),
            db_integration=integration_raw in ("1", "true", "yes", "y"),
        )

    def is_db_configured(self) -> bool:
        if self.database_url_override:
            return True
        if not self.db_server:
            return False
        if self.db_auth == "sql" and (not self.db_user or not self.db_password):
            return False
        return True

    def build_database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override

        if not self.is_db_configured():
            raise ValueError(
                "Database is not configured. Set CHURN_DB_SERVER (and SQL credentials if needed) in .env."
            )

        driver = quote_plus(self.odbc_driver)
        params = f"driver={driver}"
        if self.trust_server_certificate:
            params += "&TrustServerCertificate=yes"

        # Keep backslashes in instance names (e.g. HOST\INSTANCE) for ODBC.
        server = quote(self.db_server or "", safe="\\")
        database = quote(self.db_name, safe="")

        if self.db_auth == "windows":
            return f"mssql+pyodbc://@{server}/{database}?{params}&Trusted_Connection=yes"

        user = quote_plus(self.db_user or "")
        password = quote_plus(self.db_password or "")
        return f"mssql+pyodbc://{user}:{password}@{server}/{database}?{params}"


def get_settings() -> Settings:
    return Settings.from_env()
