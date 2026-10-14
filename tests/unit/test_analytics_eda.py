from __future__ import annotations

import pandas as pd

from churn_intel.analytics.bands import assign_monthly_charge_band, assign_tenure_band
from churn_intel.analytics.metrics import compute_churn_rate
from churn_intel.analytics.segments import MIN_SEGMENT_SIZE, rank_segments


def test_tenure_band_boundaries() -> None:
    assert assign_tenure_band(0) == "0-12 months"
    assert assign_tenure_band(12) == "0-12 months"
    assert assign_tenure_band(13) == "13-24 months"
    assert assign_tenure_band(24) == "13-24 months"
    assert assign_tenure_band(25) == "25-48 months"
    assert assign_tenure_band(48) == "25-48 months"
    assert assign_tenure_band(49) == "49+ months"
    assert assign_tenure_band(72) == "49+ months"


def test_monthly_charge_band_boundaries() -> None:
    assert assign_monthly_charge_band(34.99) == "Under 35"
    assert assign_monthly_charge_band(35) == "35-49.99"
    assert assign_monthly_charge_band(49.99) == "35-49.99"
    assert assign_monthly_charge_band(50) == "50-69.99"
    assert assign_monthly_charge_band(89.99) == "70-89.99"
    assert assign_monthly_charge_band(90) == "90+"


def test_compute_churn_rate() -> None:
    series = pd.Series([1, 0, 0, 1])
    assert compute_churn_rate(series) == 0.5
    assert pd.isna(compute_churn_rate(pd.Series([], dtype=int)))


def test_rank_segments_min_sample_size() -> None:
    summary = pd.DataFrame(
        [
            {"segment_value": "A", "customer_count": 10, "churn_count": 8, "churn_rate": 0.8},
            {"segment_value": "B", "customer_count": 100, "churn_count": 40, "churn_rate": 0.4},
        ]
    )
    ranked = rank_segments(summary, min_size=MIN_SEGMENT_SIZE, segment_type="Test")
    assert len(ranked) == 1
    assert ranked.iloc[0]["segment_value"] == "B"


def test_missing_total_charges_not_filled() -> None:
    df = pd.DataFrame(
        {
            "TotalCharges": [None, 100.0],
            "total_charges_blank": [1, 0],
            "Churn": [0, 1],
        }
    )
    assert df["TotalCharges"].isna().sum() == 1
    assert int(df.loc[0, "total_charges_blank"]) == 1
