"""Transparent retention recommendation rules (non-causal hypotheses)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recommendation:
    code: str
    text: str


def recommend_for_profile(
    *,
    contract: str,
    tenure: int,
    payment_method: str,
    online_security: str,
    tech_support: str,
    high_risk: bool,
) -> list[Recommendation]:
    if not high_risk:
        return []

    recs: list[Recommendation] = []
    if contract == "Month-to-month":
        recs.append(
            Recommendation(
                "CONTRACT_REVIEW",
                "Hypothesis: discuss contract options and value for month-to-month customers flagged at elevated risk.",
            )
        )
    if tenure <= 12:
        recs.append(
            Recommendation(
                "EARLY_LIFE_SUPPORT",
                "Hypothesis: offer onboarding check-in or early-life support for newer customers at elevated risk.",
            )
        )
    if online_security == "No":
        recs.append(
            Recommendation(
                "SECURITY_REVIEW",
                "Hypothesis: share online security options or a guided security review for at-risk customers without security add-on.",
            )
        )
    if tech_support == "No":
        recs.append(
            Recommendation(
                "TECH_SUPPORT_INFO",
                "Hypothesis: provide tech support information or troubleshooting outreach for at-risk customers without tech support.",
            )
        )
    if payment_method == "Electronic check":
        recs.append(
            Recommendation(
                "PAYMENT_EXPERIENCE",
                "Hypothesis: review billing/payment experience and mention convenient automatic payment options where appropriate.",
            )
        )
    return recs
