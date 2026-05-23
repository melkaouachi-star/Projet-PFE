"""
Class-imbalance handling strategies.

Returns a sklearn-compatible *sampler* or "class_weight" config that
can be plugged into a training pipeline.  Comparing several strategies
side-by-side is essential for a thesis: each one has a different
precision/recall trade-off and business cost profile.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
from imblearn.combine import SMOTEENN, SMOTETomek
from imblearn.over_sampling import ADASYN, SMOTE, BorderlineSMOTE
from imblearn.under_sampling import RandomUnderSampler, TomekLinks

from src.utils.logger import get_logger

log = get_logger("features.imbalance")


STRATEGY_DOCS = {
    "none":         "No resampling - baseline; relies on the model's inductive bias only.",
    "undersample":  "Random undersampling of the majority class. Fast, but throws away signal.",
    "smote":        "SMOTE - synthetic oversampling by interpolation. Risk: synthesises noise near borders.",
    "borderline":   "BorderlineSMOTE - oversamples near the decision boundary. Often better than vanilla SMOTE.",
    "adasyn":       "ADASYN - adaptive oversampling focused on hard-to-classify samples.",
    "smoteenn":     "SMOTE + Edited Nearest Neighbours cleanup. Strong on noisy fraud data.",
    "smotetomek":   "SMOTE + Tomek Links cleanup. Removes overlapping samples from both classes.",
    "tomek":        "Tomek Links only - removes ambiguous majority samples.",
    "class_weight": "No resampling: use cost-sensitive learning via class_weight='balanced'.",
}


def get_sampler(strategy: str, random_state: int = 42, sampling_ratio: float = 0.1):
    """Return an imblearn sampler. Returns None for 'none'/'class_weight'."""
    strategy = strategy.lower()
    if strategy in ("none", "class_weight"):
        return None
    if strategy == "undersample":
        return RandomUnderSampler(random_state=random_state)
    if strategy == "smote":
        return SMOTE(random_state=random_state, sampling_strategy=sampling_ratio)
    if strategy == "borderline":
        return BorderlineSMOTE(random_state=random_state, sampling_strategy=sampling_ratio)
    if strategy == "adasyn":
        return ADASYN(random_state=random_state, sampling_strategy=sampling_ratio)
    if strategy == "smoteenn":
        return SMOTEENN(random_state=random_state, sampling_strategy=sampling_ratio)
    if strategy == "smotetomek":
        return SMOTETomek(random_state=random_state, sampling_strategy=sampling_ratio)
    if strategy == "tomek":
        return TomekLinks()
    raise ValueError(f"Unknown imbalance strategy: {strategy}")


def apply_strategy(
    X: pd.DataFrame, y: pd.Series, strategy: str,
    random_state: int = 42, sampling_ratio: float = 0.1,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Apply a resampling strategy and return the new (X, y)."""
    log.info(f"Applying imbalance strategy: {strategy}")
    sampler = get_sampler(strategy, random_state, sampling_ratio)
    if sampler is None:
        return X, y
    X_res, y_res = sampler.fit_resample(X, y)
    log.info(f"Before: {np.bincount(y)} - After: {np.bincount(y_res)}")
    return pd.DataFrame(X_res, columns=X.columns), pd.Series(y_res, name=y.name)
