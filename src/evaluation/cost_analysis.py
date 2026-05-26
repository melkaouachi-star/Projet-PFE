"""
Asymmetric cost-function evaluation — the theoretical core of the thesis.

Formalization
-------------
For a model that outputs a fraud probability ``p`` and a decision threshold
``s``, the total cost on a validation set is

    C(s) = FN(s) * C_FN + FP(s) * C_FP

where

* ``FN(s)`` is the number of frauds the model misses at threshold ``s``;
* ``FP(s)`` is the number of legitimate transactions wrongly blocked;
* ``C_FN`` aggregates per-fraud costs (reimbursed amount, chargeback
  penalty, ops handling, reputational proxy);
* ``C_FP`` aggregates per-FP costs (investigation, lost margin,
  customer-dissatisfaction proxy).

The economically optimal threshold is

    s* = argmin_{s in [0, 1]} C(s)

Two costing modes are supported:

* ``fixed``       — every FN / FP costs a single configured unit value.
* ``amount_aware`` — per-fraud cost grows with the transaction amount
  (``amount * loss_factor + chargeback + handling + reputational``); per-FP
  cost stays uniform (investigation + lost margin + dissatisfaction).

This module is purely additive: it does not change ``src/training/threshold.py``
or the existing decision engine.  It exists to (a) generate the publication
artefacts requested by the thesis and (b) back the upcoming
``/api/v1/cost-analysis`` and ``/api/v1/optimal-threshold`` endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
)

from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("evaluation.cost_analysis")
sns.set_theme(style="whitegrid", context="paper")


# ----------------------------------------------------------------------
# Cost parameters
# ----------------------------------------------------------------------
@dataclass
class CostParameters:
    """Cost-function parameters parsed from ``configs/config.yaml``."""

    mode: str = "amount_aware"          # "fixed" or "amount_aware"
    currency: str = "EUR"
    c_fn: float = 250.0                 # fallback unit cost when mode == "fixed"
    c_fp: float = 12.0                  # fallback unit cost when mode == "fixed"

    # amount_aware composition of C_FN (per missed fraud)
    loss_factor: float = 1.0
    chargeback_penalty: float = 25.0
    handling_cost: float = 18.0
    reputational_proxy: float = 10.0

    # amount_aware composition of C_FP (per legit blocked)
    fp_investigation_cost: float = 8.0
    fp_lost_margin: float = 3.0
    fp_dissatisfaction: float = 1.5

    @classmethod
    def from_config(cls) -> "CostParameters":
        try:
            block = get_config().cost_analysis
        except AttributeError:
            return cls()
        return cls(
            mode=str(block.get("mode", "amount_aware")),
            currency=str(block.get("currency", "EUR")),
            c_fn=float(block.get("c_fn", 250.0)),
            c_fp=float(block.get("c_fp", 12.0)),
            loss_factor=float(block.get("loss_factor", 1.0)),
            chargeback_penalty=float(block.get("chargeback_penalty", 25.0)),
            handling_cost=float(block.get("handling_cost", 18.0)),
            reputational_proxy=float(block.get("reputational_proxy", 10.0)),
            fp_investigation_cost=float(block.get("fp_investigation_cost", 8.0)),
            fp_lost_margin=float(block.get("fp_lost_margin", 3.0)),
            fp_dissatisfaction=float(block.get("fp_dissatisfaction", 1.5)),
        )

    def fp_unit_cost(self) -> float:
        if self.mode == "fixed":
            return float(self.c_fp)
        return float(self.fp_investigation_cost + self.fp_lost_margin + self.fp_dissatisfaction)

    def fn_unit_cost(self, amount: float | None = None) -> float:
        """Per-fraud cost. ``amount`` is only consulted in amount_aware mode."""
        if self.mode == "fixed" or amount is None:
            return float(self.c_fn)
        return float(
            amount * self.loss_factor
            + self.chargeback_penalty
            + self.handling_cost
            + self.reputational_proxy
        )


@dataclass
class CostOptimum:
    name: str                # "default_0.50" / "f1" / "mcc" / "cost"
    threshold: float
    total_cost: float
    fraud_loss: float
    fp_cost: float
    tp: int
    tn: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    mcc: float


# ----------------------------------------------------------------------
# Core sweep
# ----------------------------------------------------------------------
def _threshold_grid(start: float = 0.01, stop: float = 0.99, step: float = 0.01) -> np.ndarray:
    n = int(round((stop - start) / step)) + 1
    return np.round(np.linspace(start, stop, n), 4)


def _per_threshold_costs(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    amounts: np.ndarray,
    cost_params: CostParameters,
) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """Split arrays + precompute per-fraud cost vector and FP unit cost."""
    is_fraud = (y_true == 1)
    is_legit = ~is_fraud
    fraud_amounts = amounts[is_fraud]
    fp_unit = cost_params.fp_unit_cost()

    if cost_params.mode == "fixed":
        per_fraud_cost = np.full(fraud_amounts.shape, cost_params.c_fn, dtype=float)
    else:
        per_fraud_cost = (
            fraud_amounts * cost_params.loss_factor
            + cost_params.chargeback_penalty
            + cost_params.handling_cost
            + cost_params.reputational_proxy
        )

    fraud_probas = y_proba[is_fraud]
    legit_probas = y_proba[is_legit]
    return per_fraud_cost, fp_unit, fraud_probas, legit_probas


def threshold_sweep(
    y_true: Iterable[int],
    y_proba: Iterable[float],
    amounts: Optional[Iterable[float]] = None,
    cost_params: Optional[CostParameters] = None,
    thresholds: Optional[Iterable[float]] = None,
) -> pd.DataFrame:
    """
    Sweep decision thresholds and return one row per threshold with the full
    confusion matrix, the standard fraud-detection metrics and the asymmetric
    cost decomposition.

    Columns: threshold, tp, fp, tn, fn, precision, recall, f1, mcc,
             specificity, fraud_loss, fp_cost, total_cost.
    """
    y_true = np.asarray(list(y_true), dtype=int)
    y_proba = np.asarray(list(y_proba), dtype=float)
    if y_true.shape != y_proba.shape:
        raise ValueError("y_true and y_proba must have the same shape.")

    if amounts is None:
        amounts = np.ones_like(y_proba)
    else:
        amounts = np.asarray(list(amounts), dtype=float)
        if amounts.shape != y_proba.shape:
            raise ValueError("amounts must align with y_true / y_proba.")

    params = cost_params or CostParameters.from_config()
    grid = (
        np.asarray(list(thresholds), dtype=float)
        if thresholds is not None
        else _threshold_grid(
            float(get_config_get("threshold_start", 0.01)),
            float(get_config_get("threshold_stop", 0.99)),
            float(get_config_get("threshold_step", 0.01)),
        )
    )

    per_fraud_cost, fp_unit, fraud_probas, legit_probas = _per_threshold_costs(
        y_true, y_proba, amounts, params
    )

    rows: List[dict] = []
    total_pos = int(y_true.sum())
    total_neg = int(len(y_true) - total_pos)

    for t in grid:
        # Per-threshold confusion counts via vectorised comparisons.
        fraud_predicted_pos = fraud_probas >= t
        legit_predicted_pos = legit_probas >= t

        tp = int(fraud_predicted_pos.sum())
        fn = total_pos - tp
        fp = int(legit_predicted_pos.sum())
        tn = total_neg - fp

        fraud_loss = float(per_fraud_cost[~fraud_predicted_pos].sum())  # only missed frauds
        fp_cost = float(fp * fp_unit)
        total_cost = fraud_loss + fp_cost

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        # MCC computed from the confusion counts (matches sklearn for binary).
        denom = float(
            (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        )
        mcc = ((tp * tn) - (fp * fn)) / (denom ** 0.5) if denom > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        rows.append({
            "threshold": float(round(t, 4)),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "mcc": round(mcc, 6),
            "specificity": round(specificity, 6),
            "fraud_loss": round(fraud_loss, 2),
            "fp_cost": round(fp_cost, 2),
            "total_cost": round(total_cost, 2),
        })

    return pd.DataFrame(rows)


def get_config_get(key: str, default):
    """Helper: ``cost_analysis.<key>`` with a default, never raises."""
    try:
        block = get_config().cost_analysis
        return block.get(key, default)
    except AttributeError:
        return default


# ----------------------------------------------------------------------
# Optima + comparison table
# ----------------------------------------------------------------------
def _optimum_from_row(name: str, row: pd.Series) -> CostOptimum:
    return CostOptimum(
        name=name,
        threshold=float(row["threshold"]),
        total_cost=float(row["total_cost"]),
        fraud_loss=float(row["fraud_loss"]),
        fp_cost=float(row["fp_cost"]),
        tp=int(row["tp"]), tn=int(row["tn"]),
        fp=int(row["fp"]), fn=int(row["fn"]),
        precision=float(row["precision"]),
        recall=float(row["recall"]),
        f1=float(row["f1"]),
        mcc=float(row["mcc"]),
    )


def _closest_row(sweep: pd.DataFrame, threshold: float) -> pd.Series:
    idx = (sweep["threshold"] - threshold).abs().idxmin()
    return sweep.loc[idx]


def find_optimal_thresholds(
    sweep: pd.DataFrame,
    baseline_threshold: float = 0.50,
) -> Dict[str, CostOptimum]:
    """Identify default / F1-optimal / MCC-optimal / cost-optimal thresholds."""
    if sweep.empty:
        raise ValueError("Empty sweep DataFrame.")
    return {
        "default": _optimum_from_row(f"default_{baseline_threshold:.2f}", _closest_row(sweep, baseline_threshold)),
        "f1": _optimum_from_row("f1_optimal", sweep.loc[sweep["f1"].idxmax()]),
        "mcc": _optimum_from_row("mcc_optimal", sweep.loc[sweep["mcc"].idxmax()]),
        "cost": _optimum_from_row("cost_optimal", sweep.loc[sweep["total_cost"].idxmin()]),
    }


def cost_comparison_table(
    optima: Dict[str, CostOptimum],
    pr_auc: float | None = None,
    roc_auc: float | None = None,
    model_name: str | None = None,
) -> pd.DataFrame:
    """One-row-per-strategy comparison table for thesis / Power BI."""
    baseline = optima["default"].total_cost
    rows = []
    for key, opt in optima.items():
        savings = baseline - opt.total_cost
        rows.append({
            "model": model_name,
            "strategy": opt.name,
            "threshold": round(opt.threshold, 4),
            "tp": opt.tp, "fp": opt.fp, "tn": opt.tn, "fn": opt.fn,
            "precision": round(opt.precision, 4),
            "recall": round(opt.recall, 4),
            "f1": round(opt.f1, 4),
            "mcc": round(opt.mcc, 4),
            "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
            "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
            "fraud_loss": round(opt.fraud_loss, 2),
            "fp_cost": round(opt.fp_cost, 2),
            "total_cost": round(opt.total_cost, 2),
            "savings_vs_default": round(savings, 2),
            "savings_pct_vs_default": round(100.0 * savings / baseline, 2) if baseline > 0 else 0.0,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Plot helpers — all save into reports/figures
# ----------------------------------------------------------------------
def _fig_dir() -> Path:
    out = PROJECT_ROOT / get_config().paths.reports_figures
    out.mkdir(parents=True, exist_ok=True)
    return out


def _save(fig, name: str) -> Path:
    out = _fig_dir() / name
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.info(f"Saved {out}")
    return out


def plot_cost_curve(sweep: pd.DataFrame, optima: Dict[str, CostOptimum], model_name: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(sweep["threshold"], sweep["total_cost"], lw=2, color="#3b3bd8", label="Total cost C(s)")
    ax.plot(sweep["threshold"], sweep["fraud_loss"], lw=1.2, ls="--", color="#d8423b", label="Fraud loss (FN · C_FN)")
    ax.plot(sweep["threshold"], sweep["fp_cost"], lw=1.2, ls="--", color="#3bd87a", label="False-positive cost (FP · C_FP)")
    for key, color in (("default", "#888888"), ("f1", "#f59e0b"), ("mcc", "#a855f7"), ("cost", "#16a34a")):
        opt = optima[key]
        ax.axvline(opt.threshold, color=color, lw=1.0, ls=":", alpha=0.9, label=f"{opt.name} @ {opt.threshold:.2f}")
    ax.set_xlabel("Decision threshold s")
    ax.set_ylabel("Cost")
    ax.set_title(f"Asymmetric cost vs threshold — {model_name}")
    ax.legend(loc="upper right", fontsize=8)
    return _save(fig, f"30_cost_curve_{model_name}.png")


def plot_fp_fn_curves(sweep: pd.DataFrame, model_name: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(sweep["threshold"], sweep["fn"], color="#d8423b", lw=2, label="False negatives (missed fraud)")
    ax.plot(sweep["threshold"], sweep["fp"], color="#3b7dd8", lw=2, label="False positives (legit blocked)")
    ax.set_xlabel("Decision threshold s")
    ax.set_ylabel("Count")
    ax.set_title(f"Error trade-off vs threshold — {model_name}")
    ax.legend()
    return _save(fig, f"31_fp_fn_{model_name}.png")


def plot_precision_recall_threshold(sweep: pd.DataFrame, model_name: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(sweep["threshold"], sweep["precision"], color="#3b7dd8", lw=2, label="Precision")
    ax.plot(sweep["threshold"], sweep["recall"], color="#d8423b", lw=2, label="Recall")
    ax.plot(sweep["threshold"], sweep["f1"], color="#16a34a", lw=2, label="F1")
    ax.set_xlabel("Decision threshold s")
    ax.set_ylabel("Score")
    ax.set_title(f"Precision / recall / F1 vs threshold — {model_name}")
    ax.legend()
    return _save(fig, f"32_precision_recall_threshold_{model_name}.png")


def plot_economic_gain(sweep: pd.DataFrame, baseline_threshold: float, model_name: str) -> Path:
    baseline_cost = float(_closest_row(sweep, baseline_threshold)["total_cost"])
    savings = baseline_cost - sweep["total_cost"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(sweep["threshold"], savings, color="#16a34a", lw=2)
    ax.axhline(0.0, color="grey", lw=0.8, ls="--")
    ax.set_xlabel("Decision threshold s")
    ax.set_ylabel(f"Savings vs s = {baseline_threshold:.2f}")
    ax.set_title(f"Economic gain vs default threshold — {model_name}")
    return _save(fig, f"33_economic_gain_{model_name}.png")


# ----------------------------------------------------------------------
# Convenience runner used by scripts and (Phase 3) API endpoints
# ----------------------------------------------------------------------
def run_full_analysis(
    y_true: Iterable[int],
    y_proba: Iterable[float],
    amounts: Optional[Iterable[float]] = None,
    model_name: str = "model",
    cost_params: Optional[CostParameters] = None,
    baseline_threshold: float | None = None,
    write_tables_dir: Path | str | None = None,
    write_plots: bool = True,
) -> Dict[str, object]:
    """Run sweep + optima + summary in one call. Optionally writes CSVs + PNGs."""
    params = cost_params or CostParameters.from_config()
    baseline = float(
        baseline_threshold if baseline_threshold is not None else get_config_get("baseline_threshold", 0.50)
    )

    sweep = threshold_sweep(y_true, y_proba, amounts=amounts, cost_params=params)
    optima = find_optimal_thresholds(sweep, baseline_threshold=baseline)

    y_arr = np.asarray(list(y_true), dtype=int)
    p_arr = np.asarray(list(y_proba), dtype=float)
    pr_auc = float(average_precision_score(y_arr, p_arr)) if y_arr.sum() > 0 else None
    roc_auc = float(roc_auc_score(y_arr, p_arr)) if (y_arr.sum() > 0 and y_arr.sum() < len(y_arr)) else None

    summary = cost_comparison_table(optima, pr_auc=pr_auc, roc_auc=roc_auc, model_name=model_name)

    if write_tables_dir is not None:
        tdir = Path(write_tables_dir)
        if not tdir.is_absolute():
            tdir = PROJECT_ROOT / tdir
        tdir.mkdir(parents=True, exist_ok=True)
        sweep_path = tdir / f"cost_analysis_{model_name}.csv"
        summary_path = tdir / f"threshold_optimization_{model_name}.csv"
        sweep.to_csv(sweep_path, index=False)
        summary.to_csv(summary_path, index=False)
        log.info(f"Wrote {sweep_path}")
        log.info(f"Wrote {summary_path}")

    if write_plots:
        plot_cost_curve(sweep, optima, model_name)
        plot_fp_fn_curves(sweep, model_name)
        plot_precision_recall_threshold(sweep, model_name)
        plot_economic_gain(sweep, baseline, model_name)

    return {
        "sweep": sweep,
        "optima": optima,
        "summary": summary,
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "baseline_threshold": baseline,
        "model_name": model_name,
        "cost_params": params,
    }
