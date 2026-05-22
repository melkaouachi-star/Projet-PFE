"""
Fraud-specific evaluation metrics.

We deliberately favour PR-AUC, MCC and F1 over ROC-AUC: with extreme
class imbalance (~0.17 % fraud), ROC-AUC can stay very high even when
the model is unusable in production.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Compute the canonical fraud-detection metrics."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp + 1e-12)

    return {
        "precision":        float(precision_score(y_true, y_pred, zero_division=0)),
        "recall":           float(recall_score(y_true, y_pred, zero_division=0)),
        "f1":               float(f1_score(y_true, y_pred, zero_division=0)),
        "mcc":              float(matthews_corrcoef(y_true, y_pred)),
        "roc_auc":          float(roc_auc_score(y_true, y_proba)),
        "pr_auc":           float(average_precision_score(y_true, y_proba)),
        "specificity":      float(specificity),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }
