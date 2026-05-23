"""
Baseline & gradient-boosting model factories.

Each builder returns a *fresh* untrained estimator configured via
`configs/config.yaml`.  Centralising model construction here makes
the training pipeline declarative and reproducible.
"""
from __future__ import annotations

from typing import Callable, Dict

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from src.utils.config import get_config


def build_logistic_regression(class_weight=None):
    """Logistic regression baseline.

    Notes
    -----
    - `n_jobs` was removed from sklearn LR in v1.8; we no longer pass it.
    - `lbfgs` sometimes refuses to converge on this dataset, so we
      switch to the more robust `saga` solver with a larger iteration
      budget. The data has already been RobustScaled upstream.
    """
    cfg = get_config()
    return LogisticRegression(
        solver="saga",
        max_iter=10000,
        tol=1e-3,
        class_weight=class_weight,
        random_state=cfg.project.random_seed,
    )


def build_random_forest(class_weight=None):
    cfg = get_config().models.random_forest
    base = get_config()
    return RandomForestClassifier(
        n_estimators=cfg.n_estimators,
        max_depth=cfg.max_depth,
        n_jobs=base.training.n_jobs,
        class_weight=class_weight,
        random_state=base.project.random_seed,
    )


def build_xgboost(class_weight=None):
    from xgboost import XGBClassifier
    cfg = get_config().models.xgboost
    base = get_config()
    scale_pos_weight = 1.0
    if class_weight == "balanced":
        scale_pos_weight = 99.0   # ~ majority/minority ratio for this dataset
    return XGBClassifier(
        n_estimators=cfg.n_estimators,
        max_depth=cfg.max_depth,
        learning_rate=cfg.learning_rate,
        subsample=cfg.subsample,
        colsample_bytree=cfg.colsample_bytree,
        eval_metric="aucpr",
        tree_method="hist",
        scale_pos_weight=scale_pos_weight,
        random_state=base.project.random_seed,
        n_jobs=base.training.n_jobs,
    )


def build_lightgbm(class_weight=None):
    from lightgbm import LGBMClassifier
    cfg = get_config().models.lightgbm
    base = get_config()
    return LGBMClassifier(
        n_estimators=cfg.n_estimators,
        num_leaves=cfg.num_leaves,
        learning_rate=cfg.learning_rate,
        class_weight=class_weight,
        random_state=base.project.random_seed,
        n_jobs=base.training.n_jobs,
        verbose=-1,
    )


def build_catboost(class_weight=None):
    from catboost import CatBoostClassifier
    cfg = get_config().models.catboost
    base = get_config()
    return CatBoostClassifier(
        iterations=cfg.iterations,
        depth=cfg.depth,
        learning_rate=cfg.learning_rate,
        random_seed=base.project.random_seed,
        auto_class_weights="Balanced" if class_weight == "balanced" else None,
        verbose=False,
    )


def all_builders() -> Dict[str, Callable]:
    """Return a name -> builder mapping for every enabled baseline."""
    cfg = get_config().models
    builders: Dict[str, Callable] = {}
    if cfg.logistic_regression.enabled:
        builders["logistic_regression"] = build_logistic_regression
    if cfg.random_forest.enabled:
        builders["random_forest"] = build_random_forest
    if cfg.xgboost.enabled:
        builders["xgboost"] = build_xgboost
    if cfg.lightgbm.enabled:
        builders["lightgbm"] = build_lightgbm
    if cfg.catboost.enabled:
        builders["catboost"] = build_catboost
    return builders
