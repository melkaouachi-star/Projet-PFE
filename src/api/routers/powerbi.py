"""
Power BI integration endpoints (/api/powerbi/*).

These are the **Import-mode / Web-connector fallback** for the Power BI
dashboard and a convenient health/inspection surface for the DirectQuery
views. The canonical near-real-time path is Power BI DirectQuery straight to
the ``vw_powerbi_*`` PostgreSQL views (see sql/powerbi_views_postgres.sql and
powerbi/directquery_refresh_guide.md). These JSON endpoints exist so the same
data can be consumed where a direct database connection is not available.

Design notes
------------
* This is a NEW namespace (``/api/powerbi``). It does not collide with the
  existing CSV exports (``/api/v1/export/*``) or the banking router
  (``/transactions`` etc.).
* Endpoints read the ``vw_powerbi_*`` views so there is ONE source of truth.
  If the views are missing the endpoint returns HTTP 503 with the exact
  command to create them — it never silently returns wrong data.
* Read-only: nothing here writes to the live tables. ``/export-bundle`` writes
  only into the timestamped ``exports/powerbi_bundle/`` directory.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from src.api.dependencies import get_session
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger("api.powerbi")

router = APIRouter(prefix="/api/powerbi", tags=["powerbi"])

_VIEW_MISSING_HINT = (
    "Power BI views are not present. Create them with: "
    "python scripts/load_powerbi_warehouse.py"
)


def _row_limit() -> int:
    try:
        return int(get_config().powerbi.get("api_row_limit", 50000))
    except AttributeError:
        return 50000


def _query(db: Session, sql: str, params: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Run a read-only SELECT against a view; 503 if the view is missing."""
    try:
        result = db.execute(text(sql), params or {})
        return [dict(m) for m in result.mappings().all()]
    except (ProgrammingError, OperationalError) as exc:
        # Undefined table/view — surface an actionable hint instead of a 500.
        msg = str(getattr(exc, "orig", exc)).lower()
        if "exist" in msg or "no such" in msg or "undefined" in msg:
            raise HTTPException(status_code=503, detail=_VIEW_MISSING_HINT) from exc
        raise
    except DatabaseError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Power BI query failed: {exc}") from exc


# ----------------------------------------------------------------------
# Discovery / health
# ----------------------------------------------------------------------
_VIEWS = [
    "vw_powerbi_live_transactions",
    "vw_powerbi_live_kpis",
    "vw_powerbi_fraud_alerts",
    "vw_powerbi_shap_explanations",
    "vw_powerbi_model_benchmark",
    "vw_powerbi_cost_comparison",
    "vw_powerbi_threshold_optimization",
    "vw_powerbi_simulation_effectiveness",
    "vw_powerbi_moroccan_context",
]


@router.get("/views", summary="List Power BI views and their row counts")
def list_views(db: Session = Depends(get_session)):
    out = []
    for view in _VIEWS:
        try:
            n = db.execute(text(f"SELECT COUNT(*) FROM {view}")).scalar()
            out.append({"view": view, "available": True, "rows": int(n or 0)})
        except (ProgrammingError, OperationalError):
            db.rollback()
            out.append({"view": view, "available": False, "rows": 0})
    return {"views": out, "hint": _VIEW_MISSING_HINT}


# ----------------------------------------------------------------------
# Live data
# ----------------------------------------------------------------------
@router.get("/transactions", summary="Live transactions (fact_transactions)")
def transactions(
    limit: int = Query(5000, ge=1, le=200000),
    simulation_run_id: Optional[str] = Query(None),
    db: Session = Depends(get_session),
):
    where = "WHERE simulation_run_id = :run" if simulation_run_id else ""
    sql = (
        "SELECT * FROM vw_powerbi_live_transactions "
        f"{where} ORDER BY created_at DESC LIMIT :lim"
    )
    return _query(db, sql, {"lim": min(limit, _row_limit()), "run": simulation_run_id})


@router.get("/kpis", summary="Live KPI snapshot (single row)")
def kpis(db: Session = Depends(get_session)):
    rows = _query(db, "SELECT * FROM vw_powerbi_live_kpis")
    return rows[0] if rows else {}


@router.get("/fraud-alerts", summary="Fraud alerts (fact_fraud_alerts)")
def fraud_alerts(
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_session),
):
    return _query(
        db,
        "SELECT * FROM vw_powerbi_fraud_alerts ORDER BY timestamp DESC LIMIT :lim",
        {"lim": min(limit, _row_limit())},
    )


@router.get("/shap-explanations", summary="SHAP explanations, long format")
def shap_explanations(
    limit: int = Query(20000, ge=1, le=500000),
    transaction_id: Optional[str] = Query(None),
    db: Session = Depends(get_session),
):
    where = "WHERE transaction_id = :tid" if transaction_id else ""
    sql = (
        "SELECT * FROM vw_powerbi_shap_explanations "
        f"{where} ORDER BY transaction_id, rank_importance LIMIT :lim"
    )
    return _query(db, sql, {"lim": min(limit, _row_limit()), "tid": transaction_id})


@router.get("/customers", summary="Synthetic customer profiles (dim_customer)")
def customers(
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_session),
):
    return _query(
        db,
        "SELECT * FROM banking_customers ORDER BY updated_at DESC LIMIT :lim",
        {"lim": min(limit, _row_limit())},
    )


# ----------------------------------------------------------------------
# Benchmark / cost / threshold warehouse
# ----------------------------------------------------------------------
@router.get("/model-benchmark", summary="Model benchmark (fact_model_benchmark)")
def model_benchmark(db: Session = Depends(get_session)):
    return _query(db, "SELECT * FROM vw_powerbi_model_benchmark ORDER BY model_rank")


@router.get("/cost-summary", summary="Cost comparison summary (fact_cost_analysis)")
def cost_summary(
    model_name: Optional[str] = Query(None),
    db: Session = Depends(get_session),
):
    where = "WHERE model_name = :m" if model_name else ""
    return _query(db, f"SELECT * FROM vw_powerbi_cost_comparison {where}", {"m": model_name})


@router.get(
    "/threshold-optimization/{model_name}",
    summary="Per-threshold sweep for one model (fact_threshold_optimization)",
)
def threshold_optimization(model_name: str, db: Session = Depends(get_session)):
    rows = _query(
        db,
        "SELECT * FROM vw_powerbi_threshold_optimization "
        "WHERE model_name = :m ORDER BY threshold_value",
        {"m": model_name},
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No threshold sweep for '{model_name}'. "
                "Run scripts/run_cost_analysis.py then scripts/load_powerbi_warehouse.py."
            ),
        )
    return rows


# ----------------------------------------------------------------------
# Simulation evidence + export bundle
# ----------------------------------------------------------------------
@router.get("/simulation-summary", summary="Per-run effectiveness + global KPIs")
def simulation_summary(db: Session = Depends(get_session)):
    runs = _query(
        db,
        "SELECT * FROM vw_powerbi_simulation_effectiveness ORDER BY started_at DESC",
    )
    kpi_rows = _query(db, "SELECT * FROM vw_powerbi_live_kpis")
    return {"runs": runs, "global": kpi_rows[0] if kpi_rows else {}}


@router.get("/moroccan-context", summary="Synthetic Moroccan-context demo data (labelled)")
def moroccan_context(db: Session = Depends(get_session)):
    return _query(db, "SELECT * FROM vw_powerbi_moroccan_context ORDER BY transactions DESC")


@router.post("/export-bundle", summary="Build a timestamped Power BI export bundle")
def export_bundle(
    limit: int = Query(50000, ge=1, le=500000),
    db: Session = Depends(get_session),
):
    """Generate exports/powerbi_bundle/<timestamp>/ and return its manifest."""
    try:
        from scripts.build_powerbi_bundle import build_bundle  # local import
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Bundle builder unavailable: {exc}") from exc
    manifest = build_bundle(db=db, row_limit=limit)
    return manifest
