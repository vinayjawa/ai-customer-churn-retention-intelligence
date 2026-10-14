"""SQL-backed exploratory data analysis."""

from churn_intel.analytics.bands import assign_monthly_charge_band, assign_tenure_band
from churn_intel.analytics.metrics import compute_churn_rate
from churn_intel.analytics.segments import MIN_SEGMENT_SIZE, rank_segments

__all__ = [
    "assign_monthly_charge_band",
    "assign_tenure_band",
    "compute_churn_rate",
    "MIN_SEGMENT_SIZE",
    "rank_segments",
]
