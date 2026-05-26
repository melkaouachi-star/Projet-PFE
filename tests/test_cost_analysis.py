"""Unit tests for the asymmetric cost-function module."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation.cost_analysis import (
    CostParameters,
    cost_comparison_table,
    find_optimal_thresholds,
    run_full_analysis,
    threshold_sweep,
)
from src.training.threshold import best_threshold


def _synthetic_scores(seed: int = 0, n: int = 2000, fraud_rate: float = 0.04):
    """Imbalanced binary problem where probabilities mostly track the label."""
    rng = np.random.default_rng(seed)
    n_fraud = int(n * fraud_rate)
    n_legit = n - n_fraud
    y = np.concatenate([np.zeros(n_legit, dtype=int), np.ones(n_fraud, dtype=int)])
    proba_legit = rng.beta(2, 8, size=n_legit)      # mostly low scores
    proba_fraud = rng.beta(7, 2, size=n_fraud)      # mostly high scores
    proba = np.concatenate([proba_legit, proba_fraud])
    # mild label noise so the optima are non-trivial
    proba += rng.normal(0, 0.05, size=n)
    proba = np.clip(proba, 0.0, 1.0)
    perm = rng.permutation(n)
    return y[perm], proba[perm]


def _amounts(seed: int, n: int):
    rng = np.random.default_rng(seed + 99)
    return rng.lognormal(mean=4.0, sigma=1.2, size=n).round(2)


def test_threshold_sweep_columns_and_shape():
    y, p = _synthetic_scores(seed=1)
    sweep = threshold_sweep(y, p, cost_params=CostParameters(mode="fixed", c_fn=100, c_fp=5))
    expected = {
        "threshold", "tp", "fp", "tn", "fn",
        "precision", "recall", "f1", "mcc", "specificity",
        "fraud_loss", "fp_cost", "total_cost",
    }
    assert expected.issubset(sweep.columns)
    assert (sweep["total_cost"] >= 0).all()
    # confusion-matrix invariant
    assert (sweep[["tp", "fp", "tn", "fn"]].sum(axis=1) == len(y)).all()


def test_cost_optimum_beats_default_when_fn_dominates():
    y, p = _synthetic_scores(seed=2)
    # FN is 50x more expensive than FP -> optimum should lower the threshold.
    params = CostParameters(mode="fixed", c_fn=500.0, c_fp=10.0)
    sweep = threshold_sweep(y, p, cost_params=params)
    optima = find_optimal_thresholds(sweep, baseline_threshold=0.50)

    assert optima["cost"].total_cost <= optima["default"].total_cost
    assert optima["cost"].threshold <= 0.50


def test_amount_aware_mode_uses_transaction_amounts():
    y, p = _synthetic_scores(seed=3)
    amts = _amounts(seed=3, n=len(y))
    params = CostParameters(
        mode="amount_aware",
        loss_factor=1.0,
        chargeback_penalty=25.0,
        handling_cost=10.0,
        reputational_proxy=5.0,
        fp_investigation_cost=8.0,
        fp_lost_margin=2.0,
        fp_dissatisfaction=1.0,
    )
    sweep_amt = threshold_sweep(y, p, amounts=amts, cost_params=params)
    sweep_no = threshold_sweep(y, p, cost_params=params)  # falls back to amount=1.0
    # The amount-aware sweep should produce a strictly larger fraud_loss at low
    # thresholds because frauds carry large amounts (lognormal mean ~ e^4).
    assert sweep_amt.loc[sweep_amt.threshold.between(0.4, 0.6), "fraud_loss"].sum() \
        > sweep_no.loc[sweep_no.threshold.between(0.4, 0.6), "fraud_loss"].sum()


def test_fixed_mode_agrees_with_legacy_threshold_module():
    """
    In fixed mode the cost-optimal threshold from this module should match
    src.training.threshold.best_threshold(strategy='cost_sensitive') —
    they implement the same formula with the same parameters.
    """
    y, p = _synthetic_scores(seed=4)
    # Inject costs identical to the legacy module's config defaults.
    params = CostParameters(mode="fixed", c_fn=10.0, c_fp=1.0)
    sweep = threshold_sweep(y, p, cost_params=params)
    cost_opt = find_optimal_thresholds(sweep)["cost"]

    legacy = best_threshold(y, p, strategy="cost_sensitive")
    # Both sweep the same 0.01..0.99 grid, but the cost-analysis grid has
    # finer resolution; allow one grid step of slack.
    assert abs(cost_opt.threshold - legacy.threshold) <= 0.02


def test_comparison_table_savings_columns():
    y, p = _synthetic_scores(seed=5)
    result = run_full_analysis(
        y, p,
        amounts=_amounts(5, len(y)),
        model_name="unit_test_model",
        write_plots=False,
    )
    summary: pd.DataFrame = result["summary"]
    assert {"strategy", "threshold", "total_cost", "savings_vs_default",
            "savings_pct_vs_default"}.issubset(summary.columns)
    # Default row has zero savings by construction.
    default_row = summary[summary["strategy"].str.startswith("default")].iloc[0]
    assert default_row["savings_vs_default"] == 0.0
    # cost_optimal row has savings >= 0.
    cost_row = summary[summary["strategy"] == "cost_optimal"].iloc[0]
    assert cost_row["savings_vs_default"] >= 0.0
