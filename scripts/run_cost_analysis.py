"""
CLI: run the formal asymmetric cost-function evaluation for every trained
model and write the thesis / Power BI artefacts.

For each model found in ``models_store/`` this writes:

* ``reports/tables/cost_analysis_{model}.csv``         — full per-threshold sweep
* ``reports/tables/threshold_optimization_{model}.csv`` — one row per strategy
                                                          (default / F1 / MCC / cost)
* ``reports/figures/30_cost_curve_{model}.png``
* ``reports/figures/31_fp_fn_{model}.png``
* ``reports/figures/32_precision_recall_threshold_{model}.png``
* ``reports/figures/33_economic_gain_{model}.png``

And finally one consolidated table:

* ``reports/tables/cost_comparison_summary.csv``       — every model x strategy

Usage
-----
    python scripts/run_cost_analysis.py
    python scripts/run_cost_analysis.py --model xgboost
    python scripts/run_cost_analysis.py --mode fixed --c-fn 250 --c-fp 12
    python scripts/run_cost_analysis.py --no-plots
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="sklearn")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.evaluation.cost_analysis import CostParameters, run_full_analysis
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.io import load_model
from src.utils.logger import get_logger

log = get_logger("scripts.cost_analysis")

DEFAULT_MODELS = [
    "logistic_regression", "random_forest", "xgboost",
    "lightgbm", "catboost", "voting_ensemble", "stacking_ensemble",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Asymmetric cost-function evaluation.")
    p.add_argument("--model", action="append", default=None,
                   help="Restrict to one or more model names (default: all).")
    p.add_argument("--mode", choices=["fixed", "amount_aware"], default=None,
                   help="Override cost mode (default: from config).")
    p.add_argument("--c-fn", type=float, default=None, help="Override fixed C_FN.")
    p.add_argument("--c-fp", type=float, default=None, help="Override fixed C_FP.")
    p.add_argument("--baseline", type=float, default=None,
                   help="Override baseline threshold (default: config baseline_threshold).")
    p.add_argument("--no-plots", action="store_true", help="Skip PNG generation.")
    return p.parse_args()


def _resolve_params(args) -> CostParameters:
    params = CostParameters.from_config()
    if args.mode is not None:
        params.mode = args.mode
    if args.c_fn is not None:
        params.c_fn = float(args.c_fn)
    if args.c_fp is not None:
        params.c_fp = float(args.c_fp)
    return params


def main() -> None:
    args = parse_args()
    cfg = get_config()

    test_path = PROJECT_ROOT / "data" / "processed" / "test_features.parquet"
    if not test_path.exists():
        raise FileNotFoundError(
            f"Missing {test_path}. Run scripts/run_training.py first to produce the hold-out set."
        )

    test_df = pd.read_parquet(test_path)
    target_col = cfg.data.target_column
    amount_col = cfg.data.amount_column
    y = test_df[target_col].values.astype(int)
    amounts = (
        test_df[amount_col].values.astype(float)
        if amount_col in test_df.columns
        else None
    )
    X = test_df.drop(columns=[target_col])

    params = _resolve_params(args)
    tables_dir = Path(get_config().cost_analysis.get("tables_dir", "reports/tables"))
    baseline = args.baseline if args.baseline is not None else float(
        get_config().cost_analysis.get("baseline_threshold", 0.50)
    )

    targets = args.model if args.model else DEFAULT_MODELS

    summaries = []
    for name in targets:
        try:
            model = load_model(name)
        except FileNotFoundError:
            log.warning(f"Skipping {name} (no artefact in models_store/).")
            continue
        try:
            proba = model.predict_proba(X)[:, 1]
        except Exception as exc:  # noqa: BLE001
            log.exception(f"Could not predict with {name}: {exc}")
            continue

        result = run_full_analysis(
            y_true=y,
            y_proba=proba,
            amounts=amounts,
            model_name=name,
            cost_params=params,
            baseline_threshold=baseline,
            write_tables_dir=tables_dir,
            write_plots=not args.no_plots,
        )
        summaries.append(result["summary"])

        opt = result["optima"]["cost"]
        log.info(
            f"{name:<22}  cost-opt s*={opt.threshold:.3f}  "
            f"total_cost={opt.total_cost:>10,.2f}  "
            f"savings_vs_default={(result['optima']['default'].total_cost - opt.total_cost):>10,.2f}"
        )

    if not summaries:
        log.error("No model artefacts evaluated — was training run?")
        return

    merged = pd.concat(summaries, ignore_index=True)
    out_dir = tables_dir if tables_dir.is_absolute() else PROJECT_ROOT / tables_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    merged_path = out_dir / "cost_comparison_summary.csv"
    merged.to_csv(merged_path, index=False)
    log.info(f"Consolidated cost comparison saved to {merged_path}")
    log.info("\n" + merged.to_string(index=False))


if __name__ == "__main__":
    main()
