"""
Cost-analysis and optimal-threshold REST endpoints.

Two data sources are supported:

* **offline**  — precomputed CSVs produced by ``scripts/run_cost_analysis.py``
                 (Phase 2).  This is the canonical thesis pipeline.
* **live**     — recomputed on the fly from ``banking_transactions`` rows
                 populated by the simulator, using ``scenario != "normal"``
                 as the ground-truth proxy.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_session
from src.api.schemas import (
    ComputeCostAnalysisIn,
    CostAnalysisOut,
    CostAnalysisRowOut,
    CostOptimumOut,
    OptimalThresholdOut,
)
from src.database.models import BankingTransaction
from src.evaluation.cost_analysis import (
    CostParameters,
    cost_comparison_table,
    find_optimal_thresholds,
    run_full_analysis,
    threshold_sweep,
)
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("api.cost")

router = APIRouter(prefix="/api/v1", tags=["cost-analysis"])


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _tables_dir() -> Path:
    try:
        rel = get_config().cost_analysis.get("tables_dir", "reports/tables")
    except AttributeError:
        rel = "reports/tables"
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _sweep_path(model_name: str) -> Path:
    return _tables_dir() / f"cost_analysis_{model_name}.csv"


def _summary_path(model_name: str) -> Path:
    return _tables_dir() / f"threshold_optimization_{model_name}.csv"


def _available_models() -> List[str]:
    base = _tables_dir()
    if not base.exists():
        return []
    names = []
    for p in sorted(base.glob("cost_analysis_*.csv")):
        name = p.stem.removeprefix("cost_analysis_")
        if name:
            names.append(name)
    return names


def _override_params(base: CostParameters, payload: ComputeCostAnalysisIn) -> CostParameters:
    if payload.mode is not None:
        base.mode = payload.mode
    if payload.c_fn is not None:
        base.c_fn = float(payload.c_fn)
    if payload.c_fp is not None:
        base.c_fp = float(payload.c_fp)
    return base


def _optima_payload(optima_dict) -> dict:
    return {
        key: CostOptimumOut(
            name=opt.name,
            threshold=opt.threshold,
            total_cost=opt.total_cost,
            fraud_loss=opt.fraud_loss,
            fp_cost=opt.fp_cost,
            tp=opt.tp, tn=opt.tn, fp=opt.fp, fn=opt.fn,
            precision=opt.precision, recall=opt.recall,
            f1=opt.f1, mcc=opt.mcc,
        )
        for key, opt in optima_dict.items()
    }


# ----------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------
@router.get("/cost-analysis/models", summary="List models with precomputed cost analysis")
def list_cost_models():
    return {"models": _available_models(), "tables_dir": str(_tables_dir())}


# ----------------------------------------------------------------------
# Offline cost analysis (precomputed)
# ----------------------------------------------------------------------
@router.get(
    "/cost-analysis",
    response_model=CostAnalysisOut,
    summary="Precomputed asymmetric cost analysis for one model",
)
def cost_analysis(model: str = Query(..., description="Model name (see /cost-analysis/models)")):
    sweep_path = _sweep_path(model)
    summary_path = _summary_path(model)
    if not sweep_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No precomputed cost analysis for '{model}'. "
                f"Run: python scripts/run_cost_analysis.py --model {model}"
            ),
        )
    sweep_df = pd.read_csv(sweep_path)
    summary_df = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()

    optima = find_optimal_thresholds(
        sweep_df,
        baseline_threshold=float(
            get_config().cost_analysis.get("baseline_threshold", 0.50)
        ),
    )

    params = CostParameters.from_config()
    pr_auc = roc_auc = None
    if not summary_df.empty:
        first = summary_df.iloc[0]
        pr_auc = float(first["pr_auc"]) if pd.notna(first.get("pr_auc")) else None
        roc_auc = float(first["roc_auc"]) if pd.notna(first.get("roc_auc")) else None

    return CostAnalysisOut(
        model_name=model,
        source="offline",
        mode=params.mode,
        currency=params.currency,
        baseline_threshold=optima["default"].threshold,
        pr_auc=pr_auc,
        roc_auc=roc_auc,
        optima=_optima_payload(optima),
        sweep=[CostAnalysisRowOut(**row._asdict()) for row in sweep_df.itertuples(index=False)],
        summary=summary_df.to_dict(orient="records") if not summary_df.empty else [],
    )


@router.get(
    "/optimal-threshold",
    response_model=OptimalThresholdOut,
    summary="Best decision threshold for one model under a chosen strategy",
)
def optimal_threshold(
    model: str = Query(..., description="Model name"),
    strategy: str = Query("cost", pattern="^(cost|f1|mcc|default)$"),
):
    sweep_path = _sweep_path(model)
    if not sweep_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No precomputed cost analysis for '{model}'. "
                f"Run: python scripts/run_cost_analysis.py --model {model}"
            ),
        )
    sweep_df = pd.read_csv(sweep_path)
    optima = find_optimal_thresholds(
        sweep_df,
        baseline_threshold=float(get_config().cost_analysis.get("baseline_threshold", 0.50)),
    )
    if strategy not in optima:
        raise HTTPException(status_code=400, detail=f"Unknown strategy '{strategy}'")
    opt = optima[strategy]
    return OptimalThresholdOut(
        model_name=model,
        strategy=strategy,
        source="offline",
        threshold=opt.threshold,
        total_cost=opt.total_cost,
        fraud_loss=opt.fraud_loss,
        fp_cost=opt.fp_cost,
        precision=opt.precision,
        recall=opt.recall,
        f1=opt.f1,
        mcc=opt.mcc,
        tp=opt.tp, fp=opt.fp, tn=opt.tn, fn=opt.fn,
    )


# ----------------------------------------------------------------------
# Live cost analysis — pulls fraud_probability + scenario from the
# banking_transactions table (populated by the simulator).
# ----------------------------------------------------------------------
def _live_arrays(db: Session, limit: int):
    rows = (
        db.query(
            BankingTransaction.fraud_probability,
            BankingTransaction.amount,
            BankingTransaction.scenario,
        )
        .order_by(BankingTransaction.created_at.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return None
    fraud_probs, amounts, labels = [], [], []
    for prob, amount, scenario in rows:
        if prob is None:
            continue
        # Convert the engine's 0-100 fraud_probability to a 0-1 score.
        score = float(prob) / 100.0 if float(prob) > 1.0 else float(prob)
        fraud_probs.append(score)
        amounts.append(float(amount or 0.0))
        labels.append(0 if (scenario or "normal").lower() == "normal" else 1)
    if not fraud_probs:
        return None
    return labels, fraud_probs, amounts


@router.post(
    "/cost-analysis/compute",
    response_model=CostAnalysisOut,
    summary="Recompute the cost curve from live banking transactions",
)
def compute_live_cost_analysis(
    payload: ComputeCostAnalysisIn,
    db: Session = Depends(get_session),
):
    arrays = _live_arrays(db, limit=payload.limit)
    if arrays is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No live banking transactions yet. Start the simulator: "
                "POST /api/v1/banking/simulator/start"
            ),
        )
    y_true, y_proba, amounts = arrays
    if sum(y_true) == 0 or sum(y_true) == len(y_true):
        raise HTTPException(
            status_code=409,
            detail="Live data is single-class — wait for the simulator to produce both fraud and legit transactions.",
        )

    params = _override_params(CostParameters.from_config(), payload)
    baseline = (
        float(payload.baseline_threshold)
        if payload.baseline_threshold is not None
        else float(get_config().cost_analysis.get("baseline_threshold", 0.50))
    )

    result = run_full_analysis(
        y_true=y_true,
        y_proba=y_proba,
        amounts=amounts,
        model_name=payload.model_name,
        cost_params=params,
        baseline_threshold=baseline,
        write_tables_dir=None,
        write_plots=False,
    )
    sweep_df: pd.DataFrame = result["sweep"]
    summary_df: pd.DataFrame = result["summary"]

    return CostAnalysisOut(
        model_name=payload.model_name,
        source="live",
        mode=params.mode,
        currency=params.currency,
        baseline_threshold=baseline,
        pr_auc=result["pr_auc"],
        roc_auc=result["roc_auc"],
        optima=_optima_payload(result["optima"]),
        sweep=[CostAnalysisRowOut(**row._asdict()) for row in sweep_df.itertuples(index=False)],
        summary=summary_df.to_dict(orient="records"),
    )
