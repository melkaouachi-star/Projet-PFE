"""
Bayesian hyperparameter optimisation with Optuna.

Optimises XGBoost (the strongest single learner) on PR-AUC under a
chronological CV scheme. Returns the best parameters so the training
pipeline can re-fit the final model on the full training data.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import average_precision_score
from xgboost import XGBClassifier

from src.training.validation import time_series_splits
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger("training.optimizer")
optuna.logging.set_verbosity(optuna.logging.WARNING)


def optimize_xgboost(X: pd.DataFrame, y: pd.Series, n_trials: int | None = None) -> Dict:
    """Return the best XGBoost hyperparameters."""
    base = get_config()
    n_trials = n_trials or base.optuna.n_trials

    def _objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 300, 900, step=100),
            "max_depth": trial.suggest_int("max_depth", 4, 10),
            "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, 200.0, log=True),
        }
        scores = []
        for tr, va in time_series_splits(X):
            model = XGBClassifier(
                **params,
                eval_metric="aucpr",
                tree_method="hist",
                random_state=base.project.random_seed,
                n_jobs=base.training.n_jobs,
            )
            model.fit(X.iloc[tr], y.iloc[tr], verbose=False)
            proba = model.predict_proba(X.iloc[va])[:, 1]
            scores.append(average_precision_score(y.iloc[va], proba))
        return float(np.mean(scores))

    sampler = optuna.samplers.TPESampler(seed=base.project.random_seed)
    pruner = optuna.pruners.MedianPruner()
    study = optuna.create_study(direction="maximize", sampler=sampler, pruner=pruner)
    log.info(f"Optuna study starting - {n_trials} trials.")
    study.optimize(_objective, n_trials=n_trials, timeout=base.optuna.timeout_seconds, show_progress_bar=False)
    log.info(f"Best PR-AUC: {study.best_value:.4f}")
    log.info(f"Best params : {study.best_params}")
    return study.best_params
