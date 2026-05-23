"""Tests for the threshold optimiser."""
from __future__ import annotations

import numpy as np

from src.training.threshold import best_threshold


def test_f1_threshold_returns_valid_value():
    rng = np.random.default_rng(0)
    y = (rng.random(1000) > 0.99).astype(int)
    proba = rng.random(1000)
    res = best_threshold(y, proba, strategy="f1")
    assert 0.0 <= res.threshold <= 1.0
    assert res.strategy == "f1"


def test_cost_sensitive_prefers_fewer_misses():
    """With a very high FN cost, the optimal threshold should be lower."""
    y = np.array([0]*100 + [1]*10)
    proba = np.concatenate([np.linspace(0.0, 0.6, 100), np.linspace(0.4, 0.95, 10)])
    res = best_threshold(y, proba, strategy="cost_sensitive")
    assert res.threshold < 0.9
