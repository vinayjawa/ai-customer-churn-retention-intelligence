from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from churn_intel.quality.validation import (
    EXPECTED_COLUMNS,
    REFERENCE_ROW_COUNT,
    validate_telco_csv,
)


def test_csv_structure_and_row_count(telco_csv_path: Path) -> None:
    report = validate_telco_csv(telco_csv_path)
    assert report.column_count == 21
    assert report.row_count == REFERENCE_ROW_COUNT
    assert report.passed is True
    assert report.metrics["duplicate_customer_ids"] == 0
    assert report.metrics["blank_total_charges"] == 11


def test_required_columns_order(telco_csv_path: Path) -> None:
    df = pd.read_csv(telco_csv_path, encoding="utf-8")
    assert list(df.columns) == EXPECTED_COLUMNS


def test_blank_total_charges_only_at_zero_tenure(telco_csv_path: Path) -> None:
    df = pd.read_csv(telco_csv_path, encoding="utf-8")
    blank = df["TotalCharges"].astype(str).str.strip() == ""
    assert blank.sum() == 11
    assert (df.loc[blank, "tenure"] == 0).all()


def test_invalid_churn_labels_fail_validation(tmp_path: Path, telco_csv_path: Path) -> None:
    df = pd.read_csv(telco_csv_path, encoding="utf-8", nrows=5)
    df.loc[0, "Churn"] = "Maybe"
    bad_csv = tmp_path / "bad_churn.csv"
    df.to_csv(bad_csv, index=False)
    report = validate_telco_csv(bad_csv)
    assert report.passed is False
    assert any("Invalid Churn" in err for err in report.errors)


def test_duplicate_customer_ids_fail_validation(tmp_path: Path, telco_csv_path: Path) -> None:
    df = pd.read_csv(telco_csv_path, encoding="utf-8", nrows=3)
    df.loc[2, "customerID"] = df.loc[0, "customerID"]
    dup_csv = tmp_path / "dup_ids.csv"
    df.to_csv(dup_csv, index=False)
    report = validate_telco_csv(dup_csv)
    assert report.passed is False
    assert report.metrics["duplicate_customer_ids"] == 1
