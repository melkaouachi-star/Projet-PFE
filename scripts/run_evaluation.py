"""
CLI: load every persisted model, evaluate on the chronological hold-out
and regenerate publication-quality ROC / PR / threshold / comparison
figures plus the master comparison table.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import compute_metrics
from src.evaluation.plots import (
    comparison_table,
    plot_confusion_matrix,
    plot_metric_comparison,
    plot_pr_curves,
    plot_roc_curves,
    plot_threshold_curve,
)
from src.utils.config import PROJECT_ROOT
from src.utils.io import load_model
from src.utils.logger import get_logger

log = get_logger("scripts.evaluation")

MODELS = [
    "logistic_regression", "random_forest", "xgboost",
    "lightgbm", "catboost", "voting_ensemble", "stacking_ensemble",
]


def main() -> None:
    test_path = PROJECT_ROOT / "data" / "processed" / "test_features.parquet"
    if not test_path.exists():
        raise FileNotFoundError("Run scripts/run_training.py first.")
    test_df = pd.read_parquet(test_path)
    y = test_df["Class"].values.astype(int)
    X = test_df.drop(columns=["Class"])

    probas: dict[str, np.ndarray] = {}
    reports: dict[str, dict[str, float]] = {}

    for name in MODELS:
        try:
            model = load_model(name)
        except FileNotFoundError:
            log.warning(f"Skipping {name} (not trained).")
            continue
        proba = model.predict_proba(X)[:, 1]
        probas[name] = proba
        # F1-optimal threshold per model
        from src.training.threshold import best_threshold
        thr = best_threshold(y, proba, strategy="f1").threshold
        preds = (proba >= thr).astype(int)
        m = compute_metrics(y, preds, proba)
        m["threshold"] = round(thr, 4)
        reports[name] = m
        plot_confusion_matrix(y, preds, name)
        plot_threshold_curve(y, proba, name)

    if not reports:
        log.error("No model artefacts found - did training succeed?")
        return

    df = comparison_table(reports)
    log.info("\n" + df.to_string())
    plot_roc_curves(probas, y)
    plot_pr_curves(probas, y)
    plot_metric_comparison(df)


if __name__ == "__main__":
    main()
