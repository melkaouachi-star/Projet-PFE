"""
Load the precomputed thesis CSV artefacts into the Power BI warehouse tables
and (re)create the vw_powerbi_* analytical views.

This is the bridge that makes the benchmark / cost / threshold data available
to Power BI **DirectQuery** (which needs database tables, not CSV files).

It is fully idempotent and additive:

* The 3 analytic tables (``model_benchmark_results``, ``cost_comparison_summary``,
  ``cost_analysis_sweep``) are TRUNCATED then reloaded from the CSVs, so re-runs
  never create duplicates.
* The original CSVs in ``reports/tables/`` remain the source of truth and are
  never modified.
* The live ``banking_*`` tables and the trained models are never touched.

Sources (produced by scripts/run_evaluation.py + scripts/run_cost_analysis.py):
    reports/tables/model_comparison.csv
    reports/tables/cost_comparison_summary.csv
    reports/tables/cost_analysis_{model}.csv

Usage
-----
    python scripts/load_powerbi_warehouse.py            # load + apply views
    python scripts/load_powerbi_warehouse.py --views-only
    python scripts/load_powerbi_warehouse.py --no-views
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from sqlalchemy import text

from src.database.models import (
    CostAnalysisSweep,
    CostComparisonSummary,
    ModelBenchmarkResult,
)
from src.database.session import engine, init_db, session_scope
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("scripts.load_powerbi_warehouse")


def _tables_dir() -> Path:
    try:
        rel = get_config().cost_analysis.get("tables_dir", "reports/tables")
    except AttributeError:
        rel = "reports/tables"
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _as_int(value):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------------
# Loaders
# ----------------------------------------------------------------------
def load_cost_comparison(db, base: Path) -> int:
    path = base / "cost_comparison_summary.csv"
    if not path.exists():
        log.warning(f"Missing {path.name} — run scripts/run_cost_analysis.py first. Skipping.")
        return 0
    df = pd.read_csv(path)
    db.query(CostComparisonSummary).delete()
    n = 0
    for r in df.itertuples(index=False):
        d = r._asdict()
        strategy = str(d.get("strategy", ""))
        db.add(CostComparisonSummary(
            model_name=str(d.get("model")),
            strategy=strategy,
            threshold=_as_float(d.get("threshold")),
            tp=_as_int(d.get("tp")), fp=_as_int(d.get("fp")),
            tn=_as_int(d.get("tn")), fn=_as_int(d.get("fn")),
            precision=_as_float(d.get("precision")), recall=_as_float(d.get("recall")),
            f1=_as_float(d.get("f1")), mcc=_as_float(d.get("mcc")),
            pr_auc=_as_float(d.get("pr_auc")), roc_auc=_as_float(d.get("roc_auc")),
            fraud_loss=_as_float(d.get("fraud_loss")), fp_cost=_as_float(d.get("fp_cost")),
            total_cost=_as_float(d.get("total_cost")),
            savings_vs_default=_as_float(d.get("savings_vs_default")),
            savings_pct_vs_default=_as_float(d.get("savings_pct_vs_default")),
            is_optimal_threshold=1 if "cost" in strategy.lower() else 0,
        ))
        n += 1
    return n


def load_cost_sweeps(db, base: Path) -> int:
    db.query(CostAnalysisSweep).delete()
    n = 0
    for path in sorted(base.glob("cost_analysis_*.csv")):
        model = path.stem.removeprefix("cost_analysis_")
        df = pd.read_csv(path)
        if df.empty:
            continue
        i_f1 = int(df["f1"].idxmax()) if "f1" in df else -1
        i_mcc = int(df["mcc"].idxmax()) if "mcc" in df else -1
        i_cost = int(df["total_cost"].idxmin()) if "total_cost" in df else -1
        for idx, r in enumerate(df.itertuples(index=False)):
            d = r._asdict()
            db.add(CostAnalysisSweep(
                model_name=model,
                threshold=_as_float(d.get("threshold")),
                tp=_as_int(d.get("tp")), fp=_as_int(d.get("fp")),
                tn=_as_int(d.get("tn")), fn=_as_int(d.get("fn")),
                precision=_as_float(d.get("precision")), recall=_as_float(d.get("recall")),
                f1=_as_float(d.get("f1")), mcc=_as_float(d.get("mcc")),
                specificity=_as_float(d.get("specificity")),
                fraud_loss=_as_float(d.get("fraud_loss")), fp_cost=_as_float(d.get("fp_cost")),
                total_cost=_as_float(d.get("total_cost")),
                is_f1_optimal=1 if idx == i_f1 else 0,
                is_mcc_optimal=1 if idx == i_mcc else 0,
                is_cost_optimal=1 if idx == i_cost else 0,
            ))
            n += 1
    if n == 0:
        log.warning("No cost_analysis_*.csv sweeps found — run scripts/run_cost_analysis.py.")
    return n


def load_model_benchmark(db, base: Path) -> int:
    path = base / "model_comparison.csv"
    if not path.exists():
        log.warning(f"Missing {path.name}. Skipping model benchmark load.")
        return 0
    df = pd.read_csv(path)
    df = df.rename(columns={df.columns[0]: "model_name"})

    # Enrich with cost-optimal economics when a cost summary is loaded.
    cost_by_model: dict[str, dict] = {}
    cost_path = base / "cost_comparison_summary.csv"
    if cost_path.exists():
        cdf = pd.read_csv(cost_path)
        cdf = cdf[cdf["strategy"].astype(str).str.contains("cost", case=False, na=False)]
        for r in cdf.itertuples(index=False):
            d = r._asdict()
            cost_by_model[str(d.get("model"))] = d

    db.query(ModelBenchmarkResult).delete()
    rows = []
    for r in df.itertuples(index=False):
        d = r._asdict()
        name = str(d.get("model_name"))
        cost = cost_by_model.get(name, {})
        rows.append(dict(
            model_name=name,
            precision=_as_float(d.get("precision")), recall=_as_float(d.get("recall")),
            f1=_as_float(d.get("f1")), mcc=_as_float(d.get("mcc")),
            roc_auc=_as_float(d.get("roc_auc")), pr_auc=_as_float(d.get("pr_auc")),
            specificity=_as_float(d.get("specificity")),
            balanced_accuracy=_as_float(d.get("balanced_accuracy")),
            tp=_as_int(d.get("tp")), fp=_as_int(d.get("fp")),
            tn=_as_int(d.get("tn")), fn=_as_int(d.get("fn")),
            threshold_value=_as_float(cost.get("threshold")),
            threshold_type=("cost_optimal" if cost else None),
            total_estimated_cost=_as_float(cost.get("total_cost")),
            estimated_avoided_loss=_as_float(cost.get("savings_vs_default")),
        ))

    # Rank: prefer economic cost (lower is better) when available, else MCC.
    have_cost = any(r["total_estimated_cost"] is not None for r in rows)
    if have_cost:
        rows.sort(key=lambda r: (r["total_estimated_cost"] is None, r["total_estimated_cost"] or 0.0))
    else:
        rows.sort(key=lambda r: -(r["mcc"] or 0.0))
    for rank, r in enumerate(rows, start=1):
        r["model_rank"] = rank
        r["selected_best_model"] = 1 if rank == 1 else 0
        db.add(ModelBenchmarkResult(**r))
    return len(rows)


# ----------------------------------------------------------------------
# View application
# ----------------------------------------------------------------------
def _split_statements(sql_text: str) -> list[str]:
    statements, buf = [], []
    for raw in sql_text.splitlines():
        line = raw.split("--", 1)[0] if raw.strip().startswith("--") else raw
        buf.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            buf = []
    tail = "\n".join(buf).strip().rstrip(";").strip()
    if tail:
        statements.append(tail)
    return statements


def apply_views() -> int:
    dialect = engine.dialect.name
    fname = "powerbi_views_postgres.sql" if dialect.startswith("postgre") else "powerbi_views_sqlite.sql"
    sql_file = PROJECT_ROOT / "sql" / fname
    if not sql_file.exists():
        log.error(f"View file not found: {sql_file}")
        return 0
    statements = _split_statements(sql_file.read_text(encoding="utf-8"))
    applied = 0
    with engine.begin() as conn:
        for stmt in statements:
            conn.exec_driver_sql(stmt)
            applied += 1
    log.info(f"Applied {applied} statements from {fname} ({dialect}).")
    return applied


def main() -> None:
    p = argparse.ArgumentParser(description="Load Power BI warehouse tables + views.")
    p.add_argument("--views-only", action="store_true", help="Only (re)create the views.")
    p.add_argument("--no-views", action="store_true", help="Load tables but skip view creation.")
    args = p.parse_args()

    init_db()  # ensure all tables exist (idempotent)
    base = _tables_dir()

    if not args.views_only:
        with session_scope() as db:
            n_bench = load_model_benchmark(db, base)
            n_cost = load_cost_comparison(db, base)
            n_sweep = load_cost_sweeps(db, base)
        log.info(
            f"Loaded: model_benchmark_results={n_bench}, "
            f"cost_comparison_summary={n_cost}, cost_analysis_sweep={n_sweep}"
        )

    if not args.no_views:
        apply_views()

    log.info("Power BI warehouse load complete.")


if __name__ == "__main__":
    main()
