"""CLI: python -m churn_intel.analytics"""

from __future__ import annotations

import sys

from churn_intel.analytics.eda import main

if __name__ == "__main__":
    sys.exit(main())
