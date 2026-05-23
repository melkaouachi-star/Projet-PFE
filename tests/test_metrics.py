"""Sanity tests for the fraud metrics helpers."""
from __future__ import annotations

import numpy as np

from src.evaluation.metrics import compute_metrics


def test_metrics_perfect_predictor():
    y = np.array([0, 0, 1, 1, 0, 1])
    proba = np.array([0.01, 0.02, 0.99, 0.95, 0.04, 0.97])
    pred = (proba >= 0.5).astype(int)
    m = compute_metrics(y, pred, proba)
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["mcc"] > 0.99


def test_metrics_keys_present():
    y = np.array([0, 1, 0, 1])
    proba = np.array([0.2, 0.7, 0.4, 0.9])
    pred = (proba >= 0.5).astype(int)
    m = compute_metrics(y, pred, proba)
    expected = {"precision", "recall", "f1", "mcc", "roc_auc", "pr_auc",
                "specificity", "balanced_accuracy", "tp", "fp", "tn", "fn"}
    assert expected.issubset(m.keys())
