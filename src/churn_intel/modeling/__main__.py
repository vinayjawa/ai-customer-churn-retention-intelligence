"""CLI: python -m churn_intel.modeling"""

from __future__ import annotations

import sys

from churn_intel.modeling.train import main

if __name__ == "__main__":
    sys.exit(main())
