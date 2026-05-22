"""
Ensemble architectures: soft voting, weighted voting, stacking.

Stacking is the recommended choice for credit-card fraud: it captures
the complementary strengths of tree boosters (XGB/LGBM) and the more
calibrated probabilities of logistic regression on the meta-level.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from sklearn.ensemble import StackingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression

from src.models.baseline import (
    build_catboost,
    build_lightgbm,
    build_logistic_regression,
    build_random_forest,
    build_xgboost,
)
from src.utils.config import get_config


def _base_learners(class_weight=None) -> List[Tuple[str, object]]:
    return [
        ("lr", build_logistic_regression(class_weight)),
        ("rf", build_random_forest(class_weight)),
        ("xgb", build_xgboost(class_weight)),
        ("lgbm", build_lightgbm(class_weight)),
    ]


def build_voting_ensemble(class_weight=None) -> VotingClassifier:
    cfg = get_config().models.ensemble
    learners = _base_learners(class_weight)
    return VotingClassifier(
        estimators=learners,
        voting=cfg.voting,
        weights=list(cfg.weights),
        n_jobs=get_config().training.n_jobs,
    )


def build_stacking_ensemble(class_weight=None) -> StackingClassifier:
    cfg = get_config().models.stacking
    learners = _base_learners(class_weight)
    if cfg.meta_learner == "xgboost":
        meta = build_xgboost(class_weight)
    else:
        meta = LogisticRegression(max_iter=2000, n_jobs=-1, class_weight=class_weight)
    return StackingClassifier(
        estimators=learners,
        final_estimator=meta,
        stack_method="predict_proba",
        n_jobs=get_config().training.n_jobs,
        passthrough=False,
    )


def ensemble_builders() -> Dict[str, callable]:
    """Builders for every enabled ensemble strategy."""
    cfg = get_config().models
    builders = {}
    if cfg.ensemble.enabled:
        builders["voting_ensemble"] = build_voting_ensemble
    if cfg.stacking.enabled:
        builders["stacking_ensemble"] = build_stacking_ensemble
    return builders
