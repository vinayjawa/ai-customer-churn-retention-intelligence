from __future__ import annotations

from churn_intel.config import Settings


def test_db_not_configured_without_server(monkeypatch) -> None:
    monkeypatch.delenv("CHURN_DATABASE_URL", raising=False)
    monkeypatch.delenv("CHURN_DB_SERVER", raising=False)
    settings = Settings.from_env()
    assert settings.is_db_configured() is False
