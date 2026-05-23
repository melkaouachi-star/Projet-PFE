"""
CLI entry point: run the full training pipeline.

Examples
--------
    python scripts/run_training.py
    python scripts/run_training.py --strategy smoteenn
    python scripts/run_training.py --strategy class_weight --tune
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

# Silence the repeating sklearn FutureWarnings / ConvergenceWarnings
# that flood the terminal during long CV runs.  This *only* affects
# the training script - library code keeps its full warning surface.
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="sklearn")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.training.trainer import run_training
from src.utils.logger import get_logger

log = get_logger("scripts.train")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train every enabled fraud model.")
    parser.add_argument("--strategy", default=None, help="Imbalance strategy (overrides config).")
    parser.add_argument("--tune", action="store_true", help="Run Optuna tuning of XGBoost.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports = run_training(strategy_override=args.strategy, tune=args.tune)
    log.info("---- Final model comparison ----")
    for r in reports:
        log.info(f"{r.name:<22}  F1={r.metrics['f1']:.4f}  PR-AUC={r.metrics['pr_auc']:.4f}  "
                 f"MCC={r.metrics['mcc']:.4f}  thr={r.threshold:.3f}")


if __name__ == "__main__":
    main()
