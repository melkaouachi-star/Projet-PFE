"""
Exploratory Data Analysis - generates publication-quality figures.

All figures land in `reports/figures/`. Each plot is small and
self-contained so that it can be referenced directly in a thesis
chapter without re-running the whole pipeline.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("data.eda")
sns.set_theme(style="whitegrid", context="paper")


def _fig_dir() -> Path:
    p = PROJECT_ROOT / get_config().paths.reports_figures
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save(fig, name: str) -> Path:
    out = _fig_dir() / name
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.info(f"Saved figure: {out}")
    return out


def plot_class_imbalance(df: pd.DataFrame, target: str = "Class") -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    counts = df[target].value_counts()
    sns.barplot(x=counts.index, y=counts.values, palette=["#3b7dd8", "#d8423b"], ax=ax)
    for i, v in enumerate(counts.values):
        ax.text(i, v, f"{v:,}\n({v/len(df):.3%})", ha="center", va="bottom", fontsize=10)
    ax.set_xticklabels(["Legitimate", "Fraud"])
    ax.set_ylabel("Number of transactions")
    ax.set_title("Class imbalance in the European credit-card dataset")
    ax.set_yscale("log")
    return _save(fig, "01_class_imbalance.png")


def plot_amount_distribution(df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, cls, color in zip(axes, [0, 1], ["#3b7dd8", "#d8423b"]):
        sns.histplot(df.loc[df.Class == cls, "Amount"], bins=80, color=color, ax=ax, log_scale=(False, True))
        ax.set_title(f"{'Fraud' if cls else 'Legitimate'} - Amount distribution")
        ax.set_xlabel("Amount (EUR)")
    fig.suptitle("Transaction amount distributions")
    fig.tight_layout()
    return _save(fig, "02_amount_distribution.png")


def plot_temporal_evolution(df: pd.DataFrame) -> Path:
    df = df.copy()
    df["hour"] = (df["Time"] // 3600) % 24
    hourly = df.groupby("hour")["Class"].agg(["sum", "count"])
    hourly["fraud_rate"] = hourly["sum"] / hourly["count"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))
    sns.lineplot(x=hourly.index, y=hourly["sum"], marker="o", ax=ax1, color="#d8423b")
    ax1.set_title("Fraud count by hour of day")
    ax1.set_xlabel("Hour"); ax1.set_ylabel("# Frauds")

    sns.lineplot(x=hourly.index, y=hourly["fraud_rate"], marker="o", ax=ax2, color="#7a3bd8")
    ax2.set_title("Fraud rate by hour of day")
    ax2.set_xlabel("Hour"); ax2.set_ylabel("Fraud rate")
    fig.tight_layout()
    return _save(fig, "03_temporal_evolution.png")


def plot_correlation_heatmap(df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(12, 10))
    corr = df.corr(numeric_only=True)
    sns.heatmap(corr, cmap="coolwarm", center=0, ax=ax, square=True,
                cbar_kws={"shrink": 0.6}, xticklabels=True, yticklabels=True)
    ax.set_title("Feature correlation heatmap")
    return _save(fig, "04_correlation_heatmap.png")


def plot_kde_amount(df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.kdeplot(np.log1p(df.loc[df.Class == 0, "Amount"]), label="Legitimate", color="#3b7dd8", ax=ax)
    sns.kdeplot(np.log1p(df.loc[df.Class == 1, "Amount"]), label="Fraud", color="#d8423b", ax=ax)
    ax.set_xlabel("log1p(Amount)"); ax.set_title("KDE of log-amount by class")
    ax.legend()
    return _save(fig, "05_kde_amount.png")


def plot_top_pca_boxplots(df: pd.DataFrame, top_k: int = 6) -> Path:
    """Boxplots for the PCA features most correlated with fraud."""
    pca_cols = [c for c in df.columns if c.startswith("V")]
    corr = df[pca_cols + ["Class"]].corr()["Class"].abs().sort_values(ascending=False)
    selected = corr.iloc[:top_k].index.tolist()
    melted = df[selected + ["Class"]].melt(id_vars="Class", var_name="feature", value_name="value")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.boxplot(data=melted, x="feature", y="value", hue="Class",
                palette={0: "#3b7dd8", 1: "#d8423b"}, ax=ax, showfliers=False)
    ax.set_title(f"Top-{top_k} PCA features most correlated with fraud")
    return _save(fig, "06_top_pca_boxplots.png")


def plot_velocity(df: pd.DataFrame) -> Path:
    """Approximate transaction velocity over a 5-minute rolling window."""
    df = df.sort_values("Time").copy()
    df["bucket"] = (df["Time"] // 300).astype(int)
    velocity = df.groupby("bucket").size()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(velocity.index * 5 / 60, velocity.values, color="#3b7dd8", lw=0.6)
    ax.set_xlabel("Time (hours)"); ax.set_ylabel("Transactions / 5 min")
    ax.set_title("Transaction velocity over time")
    return _save(fig, "07_velocity.png")


def run_full_eda(df: pd.DataFrame) -> dict:
    """Run all EDA plots and return their paths."""
    paths = {
        "class_imbalance": plot_class_imbalance(df),
        "amount_distribution": plot_amount_distribution(df),
        "temporal_evolution": plot_temporal_evolution(df),
        "correlation_heatmap": plot_correlation_heatmap(df),
        "kde_amount": plot_kde_amount(df),
        "top_pca_boxplots": plot_top_pca_boxplots(df),
        "velocity": plot_velocity(df),
    }
    log.info(f"Generated {len(paths)} EDA figures.")
    return paths
