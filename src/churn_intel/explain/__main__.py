"""CLI: python -m churn_intel.explain"""

from __future__ import annotations

import sys

from churn_intel.explain.global_explain import run_global_shap_analysis


def main() -> int:
    outputs = run_global_shap_analysis()
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
