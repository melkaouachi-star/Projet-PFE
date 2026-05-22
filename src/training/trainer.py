"""
End-to-end training pipeline.

Steps:
1. Load and chronologically split the dataset
2. Feature engineering & preprocessing (fit on train only - no leakage)
3. Imbalance handling (configurable strategy)
4. Train all enabled baseline and ensemble models
5. Calibrate probabilities
6. Evaluate every model on the hold-out test set
7. Pick the best decision threshold per model
8. Persist every model + the preprocessor + the feature engineer

The pipeline is *idempotent* - re-running it on the same data produces
bit-identical artefacts thanks to fixed random seeds.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.data.loader import chronological_split, load_creditcard_dataset
from src.data.preprocessor import FraudPreprocessor
from src.evaluation.metrics import compute_metrics
from src.features.engineering import FraudFeatureEngineer
from src.features.imbalance import apply_strategy
from src.models.baseline import all_builders
from src.models.calibration import calibrate
from src.models.ensemble import ensemble_builders
from src.training.threshold import best_threshold
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.io import dump_json, save_model
from src.utils.logger import get_logger

log = get_logger("training.trainer")


@dataclass
class ModelReport:
    name: str
    metrics: Dict[str, float]
    threshold: float
    training_time_sec: float
    artefact_path: str


def run_training(strategy_override: str | None = None,
                 tune: bool = False) -> List[ModelReport]:
    """Train every enabled model and return per-model reports."""
    cfg = get_config()

    # 1. Load
    df = load_creditcard_dataset()

    # 2. Chronological split
    train_df, test_df = chronological_split(df, test_size=cfg.training.test_size)
    log.info(f"Train rows: {len(train_df):,} | Test rows: {len(test_df):,}")

    target = cfg.data.target_column

    # 3. Feature engineering & preprocessing fitted ONLY on train
    fe = FraudFeatureEngineer(
        rolling_windows=tuple(cfg.feature_engineering.rolling_windows),
        enable_log_amount=cfg.feature_engineering.enable_log_amount,
        enable_is_night=cfg.feature_engineering.enable_is_night,
        enable_hour=cfg.feature_engineering.enable_hour_of_day,
        enable_rolling=cfg.feature_engineering.enable_rolling_stats,
        enable_zscore=cfg.feature_engineering.enable_amount_zscore,
        enable_velocity=cfg.feature_engineering.enable_velocity,
        enable_interaction=cfg.feature_engineering.enable_interaction,
    ).fit(train_df)

    train_feat = fe.transform(train_df)
    test_feat = fe.transform(test_df)

    pre = FraudPreprocessor().fit(train_feat.drop(columns=[target]))
    X_train = pre.transform(train_feat.drop(columns=[target]))
    X_test = pre.transform(test_feat.drop(columns=[target]))
    y_train = train_feat[target].astype(int)
    y_test = test_feat[target].astype(int)

    save_model(fe, "feature_engineer")
    save_model(pre, "preprocessor")

    # 4. Imbalance handling
    strategy = strategy_override or cfg.imbalance.default_strategy
    X_train_r, y_train_r = apply_strategy(
        X_train, y_train, strategy,
        random_state=cfg.project.random_seed,
        sampling_ratio=cfg.imbalance.sampling_ratio,
    )

    # 5. Optional Optuna tuning
    best_xgb_params: Dict | None = None
    if tune:
        from src.training.optimizer import optimize_xgboost
        best_xgb_params = optimize_xgboost(X_train_r, y_train_r)
        dump_json(best_xgb_params, PROJECT_ROOT / "reports" / "tables" / "optuna_best_params.json")

    # 6. Train every enabled model
    reports: List[ModelReport] = []
    class_weight = "balanced" if strategy == "class_weight" else None

    builders = {**all_builders(), **ensemble_builders()}
    for name, builder in builders.items():
        log.info(f"========== Training {name} (strategy={strategy}) ==========")
        t0 = time.time()
        model = builder(class_weight=class_weight) if "class_weight" in builder.__code__.co_varnames else builder()

        # Inject Optuna params into XGBoost only.
        if tune and best_xgb_params and name == "xgboost":
            for k, v in best_xgb_params.items():
                setattr(model, k, v)

        model.fit(X_train_r, y_train_r)
        elapsed = time.time() - t0

        # 7. Calibration (only for tree-based and ensemble models; skip LR)
        if cfg.calibration.enabled and name not in ("logistic_regression",):
            try:
                model = calibrate(model, X_train, y_train)
            except Exception as exc:
                log.warning(f"Calibration failed for {name}: {exc}")

        proba = model.predict_proba(X_test)[:, 1]
        thr = best_threshold(y_test.values, proba)
        preds = (proba >= thr.threshold).astype(int)

        metrics = compute_metrics(y_test.values, preds, proba)
        path = save_model(model, name)
        reports.append(ModelReport(
            name=name,
            metrics=metrics,
            threshold=thr.threshold,
            training_time_sec=round(elapsed, 2),
            artefact_path=str(path.relative_to(PROJECT_ROOT)),
        ))
        log.info(f"[{name}] threshold={thr.threshold:.3f}  F1={metrics['f1']:.4f}  "
                 f"PR-AUC={metrics['pr_auc']:.4f}  MCC={metrics['mcc']:.4f}")

    # Persist summary report
    summary = {r.name: asdict(r) for r in reports}
    dump_json(summary, PROJECT_ROOT / "reports" / "tables" / "training_summary.json")

    # Persist test features for later evaluation/SHAP scripts.
    X_test.assign(Class=y_test.values).to_parquet(
        PROJECT_ROOT / "data" / "processed" / "test_features.parquet"
    )

    log.info("Training pipeline finished.")
    return reports
