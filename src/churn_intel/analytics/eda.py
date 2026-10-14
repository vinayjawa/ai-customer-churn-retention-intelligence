"""Generate EDA plots and summary tables from analytics.customer."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from churn_intel.analytics.bands import TENURE_BAND_LABELS, add_band_columns
from churn_intel.analytics.load import load_customer_mart
from churn_intel.analytics.metrics import compute_churn_rate, segment_summary
from churn_intel.analytics.segments import MIN_SEGMENT_SIZE, rank_segments
from churn_intel.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

RANDOM_SEED = 42
ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "eda"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def _ensure_dirs() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _annotate_bar_rates(ax, labels, counts, rates) -> None:
    for idx, (lbl, n, rate) in enumerate(zip(labels, counts, rates, strict=True)):
        ax.text(
            idx,
            rate + 0.01,
            f"n={n:,}\n{rate * 100:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def run_eda() -> dict[str, Path]:
    sns.set_theme(style="whitegrid")
    _ensure_dirs()

    df = load_customer_mart()
    df = add_band_columns(df)

    outputs: dict[str, Path] = {}

    overall = pd.DataFrame(
        [
            {
                "total_customers": len(df),
                "churned_customers": int(df["Churn"].sum()),
                "retained_customers": int((df["Churn"] == 0).sum()),
                "overall_churn_rate": compute_churn_rate(df["Churn"]),
                "avg_tenure_months": float(df["tenure"].mean()),
                "null_total_charges": int(df["TotalCharges"].isna().sum()),
                "total_charges_blank_flag": int(df["total_charges_blank"].sum()),
            }
        ]
    )
    kpis_path = PROCESSED_DIR / "eda_overall_kpis.csv"
    overall.to_csv(kpis_path, index=False)
    outputs["overall_kpis"] = kpis_path

    # 1) Churn distribution
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    churn_counts = df["ChurnLabel"].value_counts().reindex(["No", "Yes"])
    axes[0].bar(churn_counts.index.astype(str), churn_counts.values, color=["#4c78a8", "#e45756"])
    axes[0].set_title("Customer count by churn status")
    axes[0].set_xlabel("Churn")
    axes[0].set_ylabel("Customers")
    for i, v in enumerate(churn_counts.values):
        axes[0].text(i, v + 50, f"n={v:,}", ha="center")

    rate = compute_churn_rate(df["Churn"])
    axes[1].bar(["Churn rate"], [rate], color="#e45756")
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Overall churn rate")
    axes[1].set_ylabel("Rate")
    axes[1].text(0, rate + 0.02, f"{rate * 100:.2f}% (n={len(df):,})", ha="center")
    fig.tight_layout()
    p1 = ARTIFACT_DIR / "01_churn_distribution.png"
    fig.savefig(p1, dpi=120)
    plt.close(fig)
    outputs["churn_distribution"] = p1

    def _rate_plot(data: pd.DataFrame, col: str, title: str, filename: str, order: list[str] | None = None):
        summary = segment_summary(data, col)
        if order:
            summary[col] = pd.Categorical(summary[col], categories=order, ordered=True)
            summary = summary.sort_values(col)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(summary[col].astype(str), summary["churn_rate"], color="#72b7b2")
        ax.set_ylim(0, min(1.0, summary["churn_rate"].max() + 0.15))
        ax.set_title(title)
        ax.set_xlabel(col)
        ax.set_ylabel("Churn rate")
        _annotate_bar_rates(ax, summary[col].astype(str), summary["customer_count"], summary["churn_rate"])
        plt.xticks(rotation=20, ha="right")
        fig.tight_layout()
        path = ARTIFACT_DIR / filename
        fig.savefig(path, dpi=120)
        plt.close(fig)
        csv_path = PROCESSED_DIR / filename.replace(".png", ".csv")
        summary.to_csv(csv_path, index=False)
        outputs[filename] = path
        outputs[csv_path.name] = csv_path

    tenure_order = [label for _, _, label in TENURE_BAND_LABELS]
    _rate_plot(
        df,
        "tenure_band",
        "Churn rate by tenure band",
        "03_churn_rate_by_tenure_band.png",
        order=tenure_order,
    )
    _rate_plot(
        df,
        "Contract",
        "Churn rate by contract type",
        "02_churn_rate_by_contract.png",
    )
    _rate_plot(
        df,
        "PaymentMethod",
        "Churn rate by payment method",
        "04_churn_rate_by_payment_method.png",
    )
    _rate_plot(
        df,
        "InternetService",
        "Churn rate by internet service",
        "05_churn_rate_by_internet_service.png",
    )

    for svc in ["OnlineSecurity", "TechSupport"]:
        _rate_plot(
            df,
            svc,
            f"Churn rate by {svc}",
            f"05_churn_rate_by_{svc.lower()}.png",
        )

    # Monthly charges distribution by churn
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.kdeplot(data=df, x="MonthlyCharges", hue="ChurnLabel", common_norm=False, ax=ax)
    ax.set_title("Monthly charges distribution by churn status")
    ax.set_xlabel("Monthly charges (USD)")
    ax.set_ylabel("Density")
    fig.tight_layout()
    p6 = ARTIFACT_DIR / "06_monthly_charges_by_churn.png"
    fig.savefig(p6, dpi=120)
    plt.close(fig)
    outputs["monthly_charges_by_churn"] = p6

    # Tenure x charge band heatmap-style table
    cross = (
        df.groupby(["tenure_band", "monthly_charge_band"], dropna=False)
        .agg(customer_count=("Churn", "size"), churn_count=("Churn", "sum"))
        .reset_index()
    )
    cross["churn_rate"] = cross["churn_count"] / cross["customer_count"].replace(0, pd.NA)
    cross_path = PROCESSED_DIR / "eda_tenure_charge_segment_summary.csv"
    cross.to_csv(cross_path, index=False)
    outputs["tenure_charge_segments"] = cross_path

    pivot = cross.pivot(index="tenure_band", columns="monthly_charge_band", values="churn_rate")
    count_pivot = cross.pivot(index="tenure_band", columns="monthly_charge_band", values="customer_count")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(pivot, annot=count_pivot.astype("Int64").astype(str), fmt="", cmap="YlOrRd", ax=ax)
    ax.set_title("Churn rate by tenure & charge band (cell text = sample size n)")
    ax.set_xlabel("Monthly charge band")
    ax.set_ylabel("Tenure band")
    fig.tight_layout()
    p7 = ARTIFACT_DIR / "07_churn_rate_tenure_charge_heatmap.png"
    fig.savefig(p7, dpi=120)
    plt.close(fig)
    outputs["tenure_charge_heatmap"] = p7

    # Ranked retention segments (Python parity with SQL script)
    ranked_frames: list[pd.DataFrame] = []
    for col, seg_type in [
        ("Contract", "Contract"),
        ("PaymentMethod", "PaymentMethod"),
        ("InternetService", "InternetService"),
        ("tenure_band", "TenureBand"),
    ]:
        summary = segment_summary(df, col).rename(columns={col: "segment_value"})
        ranked_frames.append(rank_segments(summary, segment_type=seg_type))
    ranked = pd.concat(ranked_frames, ignore_index=True)
    ranked_path = PROCESSED_DIR / "eda_retention_opportunity_ranking.csv"
    ranked.to_csv(ranked_path, index=False)
    outputs["retention_ranking"] = ranked_path

    logger.info("EDA complete: %s rows from analytics.customer", len(df))
    return outputs


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    outputs = run_eda()
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0
