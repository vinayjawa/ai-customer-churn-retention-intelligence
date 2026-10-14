"""CLI: python -m churn_intel.retention"""

from __future__ import annotations

import sys

from churn_intel.retention.analyze import run_retention_analysis


def main() -> int:
    outputs = run_retention_analysis()
    for k, p in outputs.items():
        print(f"{k}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
