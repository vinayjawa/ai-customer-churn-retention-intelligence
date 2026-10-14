"""CSV structure and domain validation (read-only on source file)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

REFERENCE_ROW_COUNT = 7043
EXPECTED_COLUMNS: list[str] = [
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
]

CATEGORICAL_DOMAINS: dict[str, set[str]] = {
    "gender": {"Female", "Male"},
    "Partner": {"No", "Yes"},
    "Dependents": {"No", "Yes"},
    "PhoneService": {"No", "Yes"},
    "MultipleLines": {"No", "No phone service", "Yes"},
    "InternetService": {"DSL", "Fiber optic", "No"},
    "OnlineSecurity": {"No", "No internet service", "Yes"},
    "OnlineBackup": {"No", "No internet service", "Yes"},
    "DeviceProtection": {"No", "No internet service", "Yes"},
    "TechSupport": {"No", "No internet service", "Yes"},
    "StreamingTV": {"No", "No internet service", "Yes"},
    "StreamingMovies": {"No", "No internet service", "Yes"},
    "Contract": {"Month-to-month", "One year", "Two year"},
    "PaperlessBilling": {"No", "Yes"},
    "PaymentMethod": {
        "Bank transfer (automatic)",
        "Credit card (automatic)",
        "Electronic check",
        "Mailed check",
    },
    "Churn": {"No", "Yes"},
}


@dataclass
class ValidationReport:
    """Aggregated validation outcome."""

    csv_path: Path
    passed: bool
    row_count: int
    column_count: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, object] = field(default_factory=dict)

    def summary_lines(self) -> list[str]:
        lines = [
            f"CSV: {self.csv_path}",
            f"Rows: {self.row_count}, Columns: {self.column_count}",
            f"Status: {'PASSED' if self.passed else 'FAILED'}",
        ]
        for key, value in sorted(self.metrics.items()):
            lines.append(f"  {key}: {value}")
        for msg in self.warnings:
            lines.append(f"WARNING: {msg}")
        for msg in self.errors:
            lines.append(f"ERROR: {msg}")
        return lines


def read_telco_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")


def validate_telco_csv(path: Path) -> ValidationReport:
    report = ValidationReport(
        csv_path=path,
        passed=True,
        row_count=0,
        column_count=0,
    )

    if not path.is_file():
        report.passed = False
        report.errors.append(f"File not found: {path}")
        return report

    try:
        df = read_telco_csv(path)
    except Exception as exc:  # noqa: BLE001 — surface read failures to report
        report.passed = False
        report.errors.append(f"Failed to read CSV as UTF-8: {exc}")
        return report

    report.row_count = len(df)
    report.column_count = len(df.columns)

    if list(df.columns) != EXPECTED_COLUMNS:
        report.passed = False
        report.errors.append(
            f"Column mismatch. Expected {len(EXPECTED_COLUMNS)} columns in order {EXPECTED_COLUMNS}; "
            f"got {list(df.columns)}."
        )

    if report.row_count != REFERENCE_ROW_COUNT:
        report.warnings.append(
            f"Row count {report.row_count} differs from reference dataset count {REFERENCE_ROW_COUNT}."
        )

    if df["customerID"].isna().any():
        report.passed = False
        report.errors.append("Null customerID values found.")

    dup_ids = int(df["customerID"].duplicated().sum())
    report.metrics["duplicate_customer_ids"] = dup_ids
    if dup_ids:
        report.passed = False
        report.errors.append(f"Duplicate customerID count: {dup_ids}")

    dup_rows = int(df.duplicated().sum())
    report.metrics["duplicate_rows"] = dup_rows
    if dup_rows:
        report.passed = False
        report.errors.append(f"Fully duplicate row count: {dup_rows}")

    invalid_churn = set(df["Churn"].dropna().unique()) - CATEGORICAL_DOMAINS["Churn"]
    report.metrics["invalid_churn_labels"] = sorted(invalid_churn)
    if invalid_churn:
        report.passed = False
        report.errors.append(f"Invalid Churn values: {sorted(invalid_churn)}")

    null_counts = df.isna().sum()
    unexpected_nulls = {col: int(null_counts[col]) for col in df.columns if null_counts[col] > 0}
    report.metrics["null_counts"] = unexpected_nulls
    if unexpected_nulls:
        report.passed = False
        report.errors.append(f"Unexpected null values: {unexpected_nulls}")

    tenure_numeric = pd.to_numeric(df["tenure"], errors="coerce")
    bad_tenure = int(tenure_numeric.isna().sum())
    report.metrics["invalid_tenure"] = bad_tenure
    if bad_tenure:
        report.passed = False
        report.errors.append(f"Non-numeric tenure values: {bad_tenure}")

    monthly_numeric = pd.to_numeric(df["MonthlyCharges"], errors="coerce")
    bad_monthly = int(monthly_numeric.isna().sum())
    report.metrics["invalid_monthly_charges"] = bad_monthly
    if bad_monthly:
        report.passed = False
        report.errors.append(f"Non-numeric MonthlyCharges values: {bad_monthly}")

    total_as_str = df["TotalCharges"].astype(str).str.strip()
    blank_total = int((total_as_str == "").sum())
    total_numeric = pd.to_numeric(df["TotalCharges"], errors="coerce")
    bad_total = int(total_numeric.isna().sum())
    report.metrics["blank_total_charges"] = blank_total
    report.metrics["non_numeric_or_blank_total_charges"] = bad_total

    if blank_total:
        blank_mask = total_as_str == ""
        tenure_at_blank = df.loc[blank_mask, "tenure"]
        non_zero_tenure = int((tenure_at_blank != 0).sum())
        report.metrics["blank_total_charges_with_nonzero_tenure"] = non_zero_tenure
        if non_zero_tenure:
            report.passed = False
            report.errors.append(
                f"{non_zero_tenure} blank TotalCharges rows have tenure != 0."
            )
        else:
            report.warnings.append(
                f"{blank_total} blank TotalCharges values; all associated with tenure=0 "
                "(will remain NULL in analytics; not coerced to zero)."
            )

    senior = pd.to_numeric(df["SeniorCitizen"], errors="coerce")
    bad_senior = int(senior.isna().sum())
    invalid_senior_vals = set(senior.dropna().unique()) - {0, 1}
    report.metrics["invalid_senior_citizen"] = bad_senior + len(invalid_senior_vals)
    if bad_senior or invalid_senior_vals:
        report.passed = False
        report.errors.append(
            f"Invalid SeniorCitizen values (non-numeric or not 0/1): count={bad_senior}, extras={invalid_senior_vals}"
        )

    for col, allowed in CATEGORICAL_DOMAINS.items():
        if col not in df.columns:
            continue
        values = set(df[col].dropna().astype(str).unique())
        extra = values - allowed
        if extra:
            report.passed = False
            report.errors.append(f"Invalid values in {col}: {sorted(extra)}")

    report.metrics["churn_yes_count"] = int((df["Churn"] == "Yes").sum())
    report.metrics["churn_no_count"] = int((df["Churn"] == "No").sum())

    return report
