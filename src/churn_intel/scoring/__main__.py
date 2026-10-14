"""CLI: python -m churn_intel.scoring [--sample N] [--no-sql]"""

from __future__ import annotations

import argparse
import logging
import sys

from churn_intel.scoring.batch import score_customers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch score customers with baseline churn model.")
    parser.add_argument("--sample", type=int, default=None, help="Score a random sample only")
    parser.add_argument("--no-sql", action="store_true", help="Skip SQL Server writes")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    _, meta = score_customers(sample_size=args.sample, write_sql=not args.no_sql)
    print(f"Rows scored: {meta['rows_scored']}")
    print(f"Output: {meta['output_csv']}")
    print(f"SQL rows written: {meta['sql_rows_written']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
