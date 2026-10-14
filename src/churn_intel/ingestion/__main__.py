"""CLI: python -m churn_intel.ingestion [--csv PATH] [--skip-ddl] [--skip-analytics]."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from churn_intel.ingestion.pipeline import run_ingestion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load telco churn CSV into SQL Server.")
    parser.add_argument("--csv", type=Path, default=None, help="Path to CSV (default: CHURN_CSV_PATH)")
    parser.add_argument("--skip-ddl", action="store_true", help="Do not run DDL scripts")
    parser.add_argument("--skip-analytics", action="store_true", help="Do not refresh analytics.customer")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    result = run_ingestion(
        csv_path=args.csv,
        apply_ddl=not args.skip_ddl,
        refresh_analytics=not args.skip_analytics,
    )

    print("\n".join(result.validation.summary_lines()))
    if result.batch_id:
        print(f"Ingest batch ID: {result.batch_id}")
    print(f"Staging rows inserted: {result.staging_rows_inserted}")
    if result.analytics_rows is not None:
        print(f"Analytics.customer rows: {result.analytics_rows}")
    if result.errors:
        print("Errors:")
        for err in result.errors:
            print(f"  - {err}")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
