"""Verify SQL Server connectivity using application configuration."""

from __future__ import annotations

import sys
from dataclasses import dataclass, replace

import pyodbc
from sqlalchemy import create_engine, text

from churn_intel.config import Settings, get_settings
from churn_intel.db import create_db_engine


def _windows_login_hint() -> str:
    try:
        master = replace(get_settings(), db_name="master")
        engine = create_engine(master.build_database_url(), future=True)
        with engine.connect() as conn:
            login = conn.execute(text("SELECT SUSER_SNAME()")).scalar()
        engine.dispose()
        return str(login)
    except Exception:
        return "your Windows account"


def detect_sql_server_odbc_driver() -> str | None:
    drivers = pyodbc.drivers()
    for preferred in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if preferred in drivers:
            return preferred
    for name in drivers:
        if "SQL Server" in name and name != "SQL Server":
            return name
    return None


def database_exists(settings: Settings) -> bool | None:
    """Return True/False if master is reachable; None if the check could not run."""
    if not settings.is_db_configured():
        return None

    master = replace(settings, db_name="master")
    engine = create_engine(master.build_database_url(), future=True)
    try:
        with engine.connect() as conn:
            found = conn.execute(
                text("SELECT 1 FROM sys.databases WHERE name = :dbname"),
                {"dbname": settings.db_name},
            ).scalar()
            return bool(found)
    except Exception:
        return None
    finally:
        engine.dispose()


@dataclass
class ConnectionCheckResult:
    success: bool
    detected_driver: str | None
    configured_driver: str
    server_name: str | None = None
    database_name: str | None = None
    login_name: str | None = None
    churn_intel_exists: bool | None = None
    message: str = ""
    error: str | None = None


def run_connection_check() -> ConnectionCheckResult:
    settings = get_settings()
    detected = detect_sql_server_odbc_driver()

    if not settings.is_db_configured():
        return ConnectionCheckResult(
            success=False,
            detected_driver=detected,
            configured_driver=settings.odbc_driver,
            message="Database settings incomplete.",
            error="Set CHURN_DB_SERVER in .env (see .env.example).",
        )

    exists = database_exists(settings)
    if exists is False:
        return ConnectionCheckResult(
            success=False,
            detected_driver=detected,
            configured_driver=settings.odbc_driver,
            churn_intel_exists=False,
            message="Windows Authentication reached SQL Server, but the target database is missing.",
            error=(
                f"Database {settings.db_name!r} was not found. Create it in SSMS for login "
                f"{_windows_login_hint()} (e.g. CREATE DATABASE ChurnIntel;), then re-run this check."
            ),
        )

    engine = create_db_engine()

    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT @@SERVERNAME AS server_name, DB_NAME() AS db_name, SUSER_SNAME() AS login_name"
                )
            ).one()
    except Exception as exc:  # noqa: BLE001 — report sanitized error to CLI
        err = str(exc).splitlines()[0]
        if "certificate" in err.lower() or "ssl" in err.lower():
            err += (
                " Certificate/encryption: use a trusted server certificate, or for local dev only "
                "set CHURN_TRUST_SERVER_CERTIFICATE=yes in .env."
            )
        return ConnectionCheckResult(
            success=False,
            detected_driver=detected,
            configured_driver=settings.odbc_driver,
            churn_intel_exists=exists,
            message="Connection failed.",
            error=err,
        )
    finally:
        engine.dispose()

    server_name = str(row.server_name)
    database_name = str(row.db_name)
    login_name = str(row.login_name)
    ok = database_name.lower() == settings.db_name.lower()

    return ConnectionCheckResult(
        success=ok,
        detected_driver=detected,
        configured_driver=settings.odbc_driver,
        server_name=server_name,
        database_name=database_name,
        login_name=login_name,
        churn_intel_exists=exists,
        message="Connection succeeded." if ok else "Connected, but not to the expected database.",
        error=None if ok else f"Expected database {settings.db_name!r}, got {database_name!r}.",
    )


def main(argv: list[str] | None = None) -> int:
    _ = argv
    result = run_connection_check()
    print(f"Detected ODBC driver: {result.detected_driver or 'none'}")
    print(f"Configured ODBC driver: {result.configured_driver}")
    if result.churn_intel_exists is not None:
        print(f"Database ChurnIntel exists (master check): {result.churn_intel_exists}")
    print(result.message)
    if result.success:
        print(f"@@SERVERNAME: {result.server_name}")
        print(f"DB_NAME(): {result.database_name}")
        print(f"SUSER_SNAME(): {result.login_name}")
    elif result.error:
        print(f"Error: {result.error}")
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
