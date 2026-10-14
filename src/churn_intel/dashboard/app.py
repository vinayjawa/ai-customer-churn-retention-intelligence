"""Streamlit dashboard — Customer Churn Prediction & Retention Intelligence."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from churn_intel.analytics.bands import assign_monthly_charge_band
from churn_intel.dashboard.constants import HIGH_RISK_QUANTILE, MODEL_PREDICTION_THRESHOLD
from churn_intel.dashboard.data import (
    SHAP_BAR_PNG,
    SHAP_SUMMARY_PNG,
    load_customers_with_bands,
    load_model_metrics,
    load_retention_tables,
    load_scores,
    load_shap_importance,
    sanitize_display_frame,
)
from churn_intel.dashboard.metrics import apply_dimension_filters, compute_overview_kpis, segment_churn_table

st.set_page_config(
    page_title="Churn Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
)

PAGES = [
    "Executive Overview",
    "Churn Analytics",
    "Churn Risk",
    "Model Performance",
    "SHAP Explainability",
    "Retention Intelligence",
]


@st.cache_data(show_spinner="Loading customer data...")
def cached_customers():
    return load_customers_with_bands()


@st.cache_data(show_spinner="Loading latest scores...")
def cached_scores(prefer_sql: bool):
    return load_scores(prefer_sql=prefer_sql)


@st.cache_data
def cached_model_metrics():
    return load_model_metrics()


@st.cache_data
def cached_shap():
    return load_shap_importance()


@st.cache_data
def cached_retention():
    return load_retention_tables()


def sidebar_filters(customers: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    page = st.sidebar.radio("Navigation", PAGES)
    prefer_sql = st.sidebar.toggle("Load scores from SQL Server", value=True)
    if st.sidebar.button("Refresh cached data"):
        st.cache_data.clear()

    contracts = st.sidebar.multiselect("Contract", sorted(customers["Contract"].unique()))
    payments = st.sidebar.multiselect("Payment method", sorted(customers["PaymentMethod"].unique()))
    internet = st.sidebar.multiselect("Internet service", sorted(customers["InternetService"].unique()))
    tenure = st.sidebar.multiselect("Tenure band", sorted(customers["tenure_band"].unique()))

    filtered = apply_dimension_filters(
        customers,
        contracts=contracts or None,
        payment_methods=payments or None,
        internet_services=internet or None,
        tenure_bands=tenure or None,
    )
    return page, prefer_sql, filtered


def render_overview(customers: pd.DataFrame, scores: pd.DataFrame, score_meta) -> None:  # score_meta: ScoreSnapshotMeta | None
    st.title("Executive Overview")
    st.caption(
        "Historical churn is observed in the dataset. Predicted probabilities are model outputs, not confirmed future churn."
    )
    kpis = compute_overview_kpis(customers, scores)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers (snapshot)", f"{kpis.get('total_customers', 0):,}")
    c2.metric("Historical churn rate", f"{kpis.get('historical_churn_rate', 0)*100:.2f}%")
    c3.metric("Avg tenure (months)", f"{kpis.get('avg_tenure', 0):.1f}")
    c4.metric("Avg monthly charges", f"${kpis.get('avg_monthly_charges', 0):,.2f}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Churned (observed)", f"{kpis.get('churned_customers', 0):,}")
    c6.metric("Retained (observed)", f"{kpis.get('retained_customers', 0):,}")
    if scores is not None and not scores.empty and score_meta is not None:
        c7.metric("Predicted churn @ 0.5", f"{kpis.get('predicted_churn_at_0_5', 0):,}")
        c8.metric(
            f"High-risk (top {int(HIGH_RISK_QUANTILE*100)}% risk)",
            f"{kpis.get('high_risk_count', 0):,} ({kpis.get('high_risk_rate', 0)*100:.1f}%)",
        )
        st.info(
            f"Latest score snapshot: {score_meta.row_count:,} rows from **{score_meta.source}**. "
            f"Timestamp: `{score_meta.scored_at_utc}` | Model: `{score_meta.model_version}`."
        )
        if score_meta.warning:
            st.warning(score_meta.warning)
    else:
        st.warning("Score snapshot unavailable. Risk KPIs hidden.")


def _bar_segment(customers: pd.DataFrame, col: str, title: str) -> None:
    table = segment_churn_table(customers, col)
    table["label"] = table[col].astype(str) + " (n=" + table["customer_count"].astype(str) + ")"
    fig = px.bar(
        table,
        x="label",
        y="churn_rate",
        hover_data=["customer_count", "churn_count"],
        title=title,
        labels={"churn_rate": "Historical churn rate", "label": col},
    )
    fig.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)


def render_analytics(customers: pd.DataFrame) -> None:
    st.title("Churn Analytics")
    st.caption("Rates use observed `Churn` labels (actual historical churn), not model predictions.")
    _bar_segment(customers, "Contract", "Historical churn rate by contract")
    _bar_segment(customers, "tenure_band", "Historical churn rate by tenure band")
    _bar_segment(customers, "PaymentMethod", "Historical churn rate by payment method")
    _bar_segment(customers, "InternetService", "Historical churn rate by internet service")
    _bar_segment(customers, "OnlineSecurity", "Historical churn rate by online security")
    _bar_segment(customers, "TechSupport", "Historical churn rate by tech support")

    work = customers.copy()
    work["monthly_charge_band"] = work["MonthlyCharges"].astype(float).map(assign_monthly_charge_band)
    _bar_segment(work, "monthly_charge_band", "Historical churn rate by monthly charge band")


def render_risk(customers: pd.DataFrame, scores: pd.DataFrame, score_meta) -> None:
    st.title("Churn Risk Overview")
    if scores.empty:
        st.error("No score snapshot available.")
        return

    merged = customers.merge(scores, on="customerID", how="inner")
    threshold = float(merged["churn_probability"].quantile(HIGH_RISK_QUANTILE))
    merged["high_risk"] = merged["churn_probability"] >= threshold
    merged["predicted_churn_label"] = (merged["churn_probability"] >= MODEL_PREDICTION_THRESHOLD).astype(int)

    st.write(
        f"Model prediction threshold: **{MODEL_PREDICTION_THRESHOLD}** | "
        f"Retention high-risk rule: **>= {threshold:.3f}** (75th percentile of predicted probability)"
    )

    fig = px.histogram(merged, x="churn_probability", nbins=40, title="Distribution of predicted churn probability")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Predicted churn @ 0.5", int((merged["predicted_churn_label"] == 1).sum()))
    c2.metric("Predicted retained @ 0.5", int((merged["predicted_churn_label"] == 0).sum()))
    c3.metric("High-risk customers", int(merged["high_risk"].sum()))

    seg = (
        merged.groupby("Contract")
        .agg(avg_risk=("churn_probability", "mean"), customers=("customerID", "size"), high_risk=("high_risk", "sum"))
        .reset_index()
        .sort_values("avg_risk", ascending=False)
    )
    st.subheader("Average predicted risk by contract")
    st.plotly_chart(px.bar(seg, x="Contract", y="avg_risk", hover_data=["customers", "high_risk"]), use_container_width=True)

    retention = cached_retention()
    anon = retention.get("high_risk_anonymized")
    if isinstance(anon, pd.DataFrame) and not anon.empty:
        st.subheader("Anonymized top-risk records (no customer IDs)")
        st.dataframe(sanitize_display_frame(anon.head(100)), use_container_width=True)


def render_model_performance() -> None:
    st.title("Model Performance")
    st.caption("Held-out test metrics from Phase 4 (`artifacts/evaluation/baseline_metrics_comparison.csv`).")
    metrics = cached_model_metrics()
    if metrics.empty:
        st.error("Metrics artifact not found.")
        return

    st.dataframe(metrics, use_container_width=True)
    plot_df = metrics.melt(id_vars=["model"], value_vars=["roc_auc", "pr_auc", "f1_churn"], var_name="metric", value_name="value")
    st.plotly_chart(px.bar(plot_df, x="model", y="value", color="metric", barmode="group", title="Test metrics comparison"), use_container_width=True)

    st.markdown(
        """
**Selected model:** Logistic Regression (balanced) — prioritizes **recall** for churn detection (0.783) with lower **precision** (0.507).
These are static test-set results, not live production monitoring.
        """
    )


def render_shap() -> None:
    st.title("SHAP Explainability")
    st.caption("Global SHAP values are in **log-odds** space for the churn class (association, not causation).")
    imp = cached_shap()
    if imp.empty:
        st.error("SHAP importance CSV not found.")
        return

    top = imp.head(15)
    st.plotly_chart(
        px.bar(top, x="mean_abs_shap", y="feature", orientation="h", title="Top features by mean |SHAP| (log-odds)"),
        use_container_width=True,
    )

    if SHAP_SUMMARY_PNG.is_file():
        st.image(str(SHAP_SUMMARY_PNG), caption="Saved SHAP summary plot (Phase 5 artifact)")
    if SHAP_BAR_PNG.is_file():
        st.image(str(SHAP_BAR_PNG), caption="Saved SHAP bar plot (Phase 5 artifact)")


def render_retention() -> None:
    st.title("Retention Intelligence")
    st.caption("Recommendations are hypotheses for investigation, not proven interventions. ROI unavailable.")
    data = cached_retention()
    meta = data.get("metadata_text")
    if meta:
        st.code(meta)

    segments = data.get("segments")
    if isinstance(segments, pd.DataFrame) and not segments.empty:
        st.subheader("Segment summary")
        st.dataframe(segments, use_container_width=True)
        st.plotly_chart(
            px.bar(segments.head(12), x="segment_value", y="high_risk_count", color="segment_type", title="High-risk volume by segment"),
            use_container_width=True,
        )

    recs = data.get("recommendations")
    if isinstance(recs, pd.DataFrame) and not recs.empty:
        st.subheader("Recommendation eligibility (high-risk customers)")
        st.dataframe(recs, use_container_width=True)


def main() -> None:
    st.sidebar.title("Churn Intelligence")
    st.sidebar.markdown(
        "Portfolio demo dashboard for SQL-backed analytics, baseline ML, SHAP, and retention intelligence."
    )

    try:
        customers = cached_customers()
    except Exception:
        st.error("Unable to load customer data. Check SQL connectivity and .env configuration.")
        st.stop()

    page, prefer_sql, filtered = sidebar_filters(customers)
    try:
        scores, score_meta = cached_scores(prefer_sql)
    except Exception:
        scores, score_meta = pd.DataFrame(), None

    scores_view = (
        scores[scores["customerID"].isin(filtered["customerID"])]
        if not scores.empty
        else scores
    )
    if page == "Executive Overview":
        render_overview(filtered, scores_view, score_meta)
    elif page == "Churn Analytics":
        render_analytics(filtered)
    elif page == "Churn Risk":
        render_risk(filtered, scores_view, score_meta)
    elif page == "Model Performance":
        render_model_performance()
    elif page == "SHAP Explainability":
        render_shap()
    elif page == "Retention Intelligence":
        render_retention()

    with st.expander("Limitations"):
        st.markdown(
            """
- Local portfolio demo; not production-ready.
- Predicted probabilities are **not** confirmed future churn.
- High-risk flag uses the **75th percentile** rule (Phase 5), separate from the **0.5** model label threshold.
- SHAP shows log-odds contributions, not guaranteed probability impact.
- No financial ROI or causal claims.
            """
        )


if __name__ == "__main__":
    main()
