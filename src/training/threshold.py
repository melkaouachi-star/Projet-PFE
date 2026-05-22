"""
Decision-threshold optimisation.

The default 0.5 threshold is almost never correct on an imbalanced
fraud problem.  We expose four strategies:
- f1:           maximise F1 score
- mcc:          maximise Matthews correlation coefficient
- cost_sensitive: minimise expected cost = fp_cost * FP + fn_cost * FN
- business:     same as cost_sensitive, but with cost values from config
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    f1_score,
    matthews_corrcoef,
    precision_recall_curve,
)

from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger("training.threshold")


@dataclass
class ThresholdResult:
    threshold: float
    score: float
    strategy: str


def best_threshold(y_true: np.ndarray, y_proba: np.ndarray,
                   strategy: str | None = None) -> ThresholdResult:
    cfg = get_config().threshold
    strategy = (strategy or cfg.strategy).lower()

    precisions, recalls, thr = precision_recall_curve(y_true, y_proba)
    thr = np.append(thr, 1.0)  # align array length

    if strategy == "f1":
        f1 = 2 * precisions * recalls / (precisions + recalls + 1e-12)
        idx = int(np.nanargmax(f1))
        return ThresholdResult(float(thr[idx]), float(f1[idx]), "f1")

    if strategy == "mcc":
        best_mcc, best_t = -1.0, 0.5
        for t in np.linspace(0.01, 0.99, 99):
            preds = (y_proba >= t).astype(int)
            score = matthews_corrcoef(y_true, preds)
            if score > best_mcc:
                best_mcc, best_t = score, t
        return ThresholdResult(float(best_t), float(best_mcc), "mcc")

    if strategy in ("cost_sensitive", "business"):
        fp_cost, fn_cost = cfg.fp_cost, cfg.fn_cost
        best_cost, best_t = np.inf, 0.5
        for t in np.linspace(0.01, 0.99, 99):
            preds = (y_proba >= t).astype(int)
            fp = int(((preds == 1) & (y_true == 0)).sum())
            fn = int(((preds == 0) & (y_true == 1)).sum())
            cost = fp * fp_cost + fn * fn_cost
            if cost < best_cost:
                best_cost, best_t = cost, t
        log.info(f"Best business threshold = {best_t:.3f} (cost={best_cost:.0f})")
        return ThresholdResult(float(best_t), -float(best_cost), strategy)

    raise ValueError(f"Unknown threshold strategy: {strategy}")
