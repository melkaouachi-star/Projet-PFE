"""
Publication-quality evaluation figures.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    auc,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)

from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("evaluation.plots")
sns.set_theme(style="whitegrid", context="paper")


def _fig_dir() -> Path:
    p = PROJECT_ROOT / get_config().paths.reports_figures
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save(fig, name: str) -> Path:
    out = _fig_dir() / name
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.info(f"Saved {out}")
    return out


def plot_roc_curves(probas: Dict[str, np.ndarray], y_true: np.ndarray) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))
    for name, proba in probas.items():
        fpr, tpr, _ = roc_curve(y_true, proba)
        ax.plot(fpr, tpr, lw=2, label=f"{name} (AUC = {auc(fpr, tpr):.4f})")
    ax.plot([0, 1], [0, 1], lw=1, ls="--", color="grey")
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC curves - chronological hold-out")
    ax.legend(loc="lower right")
    return _save(fig, "20_roc_curves.png")


def plot_pr_curves(probas: Dict[str, np.ndarray], y_true: np.ndarray) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))
    for name, proba in probas.items():
        p, r, _ = precision_recall_curve(y_true, proba)
        ax.plot(r, p, lw=2, label=f"{name} (AP = {auc(r, p):.4f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall curves")
    ax.legend(loc="lower left")
    return _save(fig, "21_pr_curves.png")


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, name: str) -> Path:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4.5, 4))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Legit", "Fraud"])
    disp.plot(ax=ax, cmap="Blues", colorbar=False, values_format="d")
    ax.set_title(f"Confusion matrix - {name}")
    return _save(fig, f"22_cm_{name}.png")


def plot_threshold_curve(y_true: np.ndarray, y_proba: np.ndarray, model_name: str) -> Path:
    thresholds = np.linspace(0.01, 0.99, 99)
    f1s, precisions, recalls = [], [], []
    for t in thresholds:
        preds = (y_proba >= t).astype(int)
        tp = ((preds == 1) & (y_true == 1)).sum()
        fp = ((preds == 1) & (y_true == 0)).sum()
        fn = ((preds == 0) & (y_true == 1)).sum()
        prec = tp / (tp + fp + 1e-12)
        rec = tp / (tp + fn + 1e-12)
        f1 = 2 * prec * rec / (prec + rec + 1e-12)
        f1s.append(f1); precisions.append(prec); recalls.append(rec)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(thresholds, precisions, label="Precision", color="#3b7dd8")
    ax.plot(thresholds, recalls, label="Recall", color="#d8423b")
    ax.plot(thresholds, f1s, label="F1", color="#3bd87a", lw=2)
    ax.set_xlabel("Decision threshold"); ax.set_ylabel("Score")
    ax.set_title(f"Threshold optimisation curve - {model_name}")
    ax.legend()
    return _save(fig, f"23_threshold_{model_name}.png")


def plot_metric_comparison(report_df: pd.DataFrame) -> Path:
    """Bar plot comparing F1, MCC, PR-AUC across models."""
    metrics = ["f1", "mcc", "pr_auc", "recall", "precision"]
    melted = report_df.reset_index().melt(
        id_vars="index", value_vars=metrics, var_name="metric", value_name="score")
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=melted, x="index", y="score", hue="metric", ax=ax)
    ax.set_xlabel("Model"); ax.set_ylabel("Score")
    ax.set_title("Comparison of fraud-detection metrics across models")
    ax.legend(loc="upper right")
    plt.xticks(rotation=30)
    return _save(fig, "24_metric_comparison.png")


def comparison_table(reports: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """Build the final per-model comparison table."""
    df = pd.DataFrame(reports).T
    df = df[["precision", "recall", "f1", "mcc",
             "roc_auc", "pr_auc", "specificity",
             "balanced_accuracy", "tp", "fp", "tn", "fn"]]
    out = PROJECT_ROOT / "reports" / "tables" / "model_comparison.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out)
    log.info(f"Comparison table saved to {out}")
    return df
