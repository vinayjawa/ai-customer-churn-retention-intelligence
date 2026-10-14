from __future__ import annotations

from pathlib import Path

import pytest

from churn_intel.config import PROJECT_ROOT


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def telco_csv_path(project_root: Path) -> Path:
    path = project_root / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    if not path.is_file():
        fallback = project_root / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
        if fallback.is_file():
            return fallback
    return path
