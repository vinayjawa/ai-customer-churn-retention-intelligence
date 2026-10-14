from __future__ import annotations

import pandas as pd

from churn_intel.dashboard.data import sanitize_display_frame, select_latest_score_batch
from churn_intel.dashboard.metrics import compute_overview_kpis, segment_churn_table
from tests.unit.test_modeling import _synthetic_frame


def test_latest_score_batch_selects_most_recent_only() -> None:
    history = pd.DataFrame(
        {
            "customerID": ["A", "B", "A", "B"],
            "churn_probability": [0.2, 0.3, 0.9, 0.8],
            "scored_at_utc": [
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
                "2026-02-01T00:00:00+00:00",
                "2026-02-01T00:00:00+00:00",
            ],
            "model_version": ["v1", "v1", "v2", "v2"],
        }
    )
    latest, meta = select_latest_score_batch(history)
    assert len(latest) == 2
    assert meta.distinct_customers == 2
    assert set(latest["churn_probability"]) == {0.9, 0.8}


def test_overview_kpis_and_high_risk_threshold() -> None:
    customers = _synthetic_frame(200)
    scores = pd.DataFrame(
        {
            "customerID": customers["customerID"],
            "churn_probability": pd.Series(range(200), dtype=float) / 200,
            "predicted_churn": 0,
        }
    )
    kpis = compute_overview_kpis(customers, scores)
    assert kpis["total_customers"] == 200
    assert 0 <= kpis["historical_churn_rate"] <= 1
    assert kpis["high_risk_count"] == 50  # top 25% of 200


def test_segment_churn_table_has_counts() -> None:
    customers = _synthetic_frame(100)
    table = segment_churn_table(customers, "Contract")
    assert "customer_count" in table.columns
    assert table["customer_count"].sum() == 100


def test_sanitize_removes_customer_id() -> None:
    df = pd.DataFrame({"customerID": ["x"], "Contract": ["Month-to-month"]})
    out = sanitize_display_frame(df)
    assert "customerID" not in out.columns
