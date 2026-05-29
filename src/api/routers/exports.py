"""
CSV / Power BI export endpoints.

Two source families:

* **Live banking tables** — streamed straight from ``banking_transactions``,
  ``banking_alerts`` and ``banking_shap_explanations`` populated by the
  simulator + the dynamic scoring engine.
* **Precomputed reports/tables** — the thesis artefacts written by
  ``scripts/run_cost_analysis.py`` and ``scripts/run_evaluation.py``.

Power BI can connect directly to PostgreSQL in production; these CSV /
ZIP endpoints exist for the offline workflow and for the dashboard's
"Download data" actions.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.api.dependencies import get_session
from src.api.schemas import ExportInventoryItem, ExportInventoryOut
from src.database.models import (
    BankingAlert,
    BankingCustomer,
    BankingTransaction,
    ShapExplanationRecord,
)
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("api.exports")

router = APIRouter(prefix="/api/v1/export", tags=["exports"])


# ----------------------------------------------------------------------
# CSV building helpers
# ----------------------------------------------------------------------
def _csv_response(rows: Iterable[dict], columns: List[str], filename: str) -> StreamingResponse:
    """Stream rows as a CSV download."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        # JSON-encode any list/dict values for CSV friendliness.
        safe = {
            k: (json.dumps(v, default=str) if isinstance(v, (list, dict)) else v)
            for k, v in row.items()
            if k in columns
        }
        writer.writerow(safe)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _empty_csv(columns: List[str], filename: str) -> StreamingResponse:
    return _csv_response([], columns, filename)


def _tables_dir() -> Path:
    try:
        rel = get_config().cost_analysis.get("tables_dir", "reports/tables")
    except AttributeError:
        rel = "reports/tables"
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _read_csv_bytes(path: Path) -> bytes:
    return path.read_bytes()


# ----------------------------------------------------------------------
# Column dictionaries — kept stable for Power BI binding
# ----------------------------------------------------------------------
TX_COLUMNS = [
    "transaction_id", "customer_id", "customer_name", "timestamp",
    "country", "city", "latitude", "longitude", "ip_address",
    "amount", "currency", "merchant_name", "merchant_category", "scenario",
    "fraud_probability", "risk_score", "fraud_level", "decision",
    "transaction_status", "model_version", "created_at",
]

ALERT_COLUMNS = [
    "transaction_id", "customer_id", "customer_name", "severity",
    "fraud_level", "risk_score", "fraud_probability", "decision",
    "amount", "currency", "country", "city", "ip_address",
    "message", "top_reasons", "created_at",
]

SHAP_COLUMNS = [
    "transaction_id", "base_value", "feature_names",
    "shap_values", "top_reasons", "risk_contribution_score", "created_at",
]

CUSTOMER_COLUMNS = [
    "customer_id", "full_name", "age", "country", "city",
    "latitude", "longitude", "account_age_days", "average_spending",
    "risk_profile", "behavior_pattern", "known_devices",
    "usual_countries", "fraud_history_count", "updated_at",
]


# ----------------------------------------------------------------------
# Inventory
# ----------------------------------------------------------------------
def _inventory_items(db: Session) -> List[ExportInventoryItem]:
    base = _tables_dir()
    bench = base / "model_comparison.csv"
    cost_summary = base / "cost_comparison_summary.csv"
    return [
        ExportInventoryItem(
            name="banking_transactions",
            rows=db.query(BankingTransaction).count(),
            available=True,
            endpoint="/api/v1/export/transactions.csv",
            description="Live transactions + scoring written by the simulator.",
        ),
        ExportInventoryItem(
            name="banking_fraud_alerts",
            rows=db.query(BankingAlert).count(),
            available=True,
            endpoint="/api/v1/export/fraud-alerts.csv",
            description="Real-time fraud alerts produced by the scoring engine.",
        ),
        ExportInventoryItem(
            name="banking_shap_explanations",
            rows=db.query(ShapExplanationRecord).count(),
            available=True,
            endpoint="/api/v1/export/shap-summary.csv",
            description="Per-transaction SHAP-style feature contributions.",
        ),
        ExportInventoryItem(
            name="banking_customers",
            rows=db.query(BankingCustomer).count(),
            available=True,
            endpoint="/api/v1/export/customers.csv",
            description="Synthetic customer profiles.",
        ),
        ExportInventoryItem(
            name="model_benchmark_results",
            available=bench.exists(),
            endpoint="/api/v1/export/model-benchmark.csv",
            description="Per-model precision/recall/F1/MCC/PR-AUC table from run_evaluation.py.",
        ),
        ExportInventoryItem(
            name="cost_comparison_summary",
            available=cost_summary.exists(),
            endpoint="/api/v1/export/cost-comparison-summary.csv",
            description="Default vs F1 vs MCC vs cost-optimal thresholds across all models.",
        ),
        ExportInventoryItem(
            name="cost_analysis_{model}",
            available=any(base.glob("cost_analysis_*.csv")) if base.exists() else False,
            endpoint="/api/v1/export/cost-analysis.csv?model=<name>",
            description="Full per-threshold sweep CSV for one model.",
        ),
        ExportInventoryItem(
            name="threshold_optimization_{model}",
            available=any(base.glob("threshold_optimization_*.csv")) if base.exists() else False,
            endpoint="/api/v1/export/threshold-optimization.csv?model=<name>",
            description="Key thresholds (default/F1/MCC/cost) for one model.",
        ),
        ExportInventoryItem(
            name="powerbi_bundle",
            available=True,
            endpoint="/api/v1/export/powerbi.zip",
            description="ZIP bundle of every CSV above (live + precomputed).",
        ),
    ]


@router.get("/inventory", response_model=ExportInventoryOut, summary="List every export endpoint")
def export_inventory(db: Session = Depends(get_session)):
    return ExportInventoryOut(items=_inventory_items(db))


# ----------------------------------------------------------------------
# Live CSV endpoints
# ----------------------------------------------------------------------
def _serialize_tx_row(t: BankingTransaction) -> dict:
    amount = t.amount if t.amount is not None else t.transaction_amount
    currency = t.currency or t.transaction_currency or "USD"
    return {
        "transaction_id": t.transaction_id,
        "customer_id": t.customer_id,
        "customer_name": t.customer_name,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
        "country": t.country, "city": t.city,
        "latitude": t.latitude, "longitude": t.longitude,
        "ip_address": t.ip_address,
        "amount": float(amount or 0.0), "currency": currency,
        "merchant_name": t.merchant_name, "merchant_category": t.merchant_category,
        "scenario": t.scenario,
        "fraud_probability": t.fraud_probability,
        "risk_score": t.risk_score, "fraud_level": t.fraud_level,
        "decision": t.decision, "transaction_status": t.transaction_status,
        "model_version": t.model_version,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


def _serialize_alert_row(a: BankingAlert) -> dict:
    return {
        "transaction_id": a.transaction_id,
        "customer_id": a.customer_id, "customer_name": a.customer_name,
        "severity": a.severity, "fraud_level": a.fraud_level,
        "risk_score": a.risk_score, "fraud_probability": a.fraud_probability,
        "decision": a.decision, "amount": a.amount, "currency": a.currency,
        "country": a.country, "city": a.city, "ip_address": a.ip_address,
        "message": a.message, "top_reasons": a.top_reasons or [],
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _serialize_shap_row(s: ShapExplanationRecord) -> dict:
    return {
        "transaction_id": s.transaction_id,
        "base_value": s.base_value,
        "feature_names": s.feature_names,
        "shap_values": s.shap_values,
        "top_reasons": s.top_reasons,
        "risk_contribution_score": s.risk_contribution_score,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _serialize_customer_row(c: BankingCustomer) -> dict:
    return {
        "customer_id": c.customer_id, "full_name": c.full_name, "age": c.age,
        "country": c.country, "city": c.city,
        "latitude": c.latitude, "longitude": c.longitude,
        "account_age_days": c.account_age_days,
        "average_spending": c.average_spending,
        "risk_profile": c.risk_profile, "behavior_pattern": c.behavior_pattern,
        "known_devices": c.known_devices or [],
        "usual_countries": c.usual_countries or [],
        "fraud_history_count": c.fraud_history_count,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("/transactions.csv", summary="Live banking transactions as CSV")
def export_transactions(
    limit: int = Query(10000, ge=1, le=200000),
    db: Session = Depends(get_session),
):
    rows = (
        db.query(BankingTransaction)
        .order_by(desc(BankingTransaction.created_at))
        .limit(limit)
        .all()
    )
    return _csv_response(
        (_serialize_tx_row(r) for r in rows),
        TX_COLUMNS,
        f"transactions_simulated_{_stamp()}.csv",
    )


@router.get("/fraud-alerts.csv", summary="Live fraud alerts as CSV")
def export_fraud_alerts(
    limit: int = Query(10000, ge=1, le=200000),
    db: Session = Depends(get_session),
):
    rows = (
        db.query(BankingAlert)
        .order_by(desc(BankingAlert.created_at))
        .limit(limit)
        .all()
    )
    return _csv_response(
        (_serialize_alert_row(r) for r in rows),
        ALERT_COLUMNS,
        f"fraud_alerts_{_stamp()}.csv",
    )


@router.get("/shap-summary.csv", summary="SHAP-style explanations as CSV")
def export_shap_summary(
    limit: int = Query(10000, ge=1, le=200000),
    db: Session = Depends(get_session),
):
    rows = (
        db.query(ShapExplanationRecord)
        .order_by(desc(ShapExplanationRecord.created_at))
        .limit(limit)
        .all()
    )
    return _csv_response(
        (_serialize_shap_row(r) for r in rows),
        SHAP_COLUMNS,
        f"shap_summary_{_stamp()}.csv",
    )


@router.get("/customers.csv", summary="Synthetic customer profiles as CSV")
def export_customers(
    limit: int = Query(10000, ge=1, le=200000),
    db: Session = Depends(get_session),
):
    rows = db.query(BankingCustomer).limit(limit).all()
    return _csv_response(
        (_serialize_customer_row(r) for r in rows),
        CUSTOMER_COLUMNS,
        f"customers_{_stamp()}.csv",
    )


# ----------------------------------------------------------------------
# Precomputed thesis-artefact CSVs
# ----------------------------------------------------------------------
def _stream_file(path: Path, filename: str) -> StreamingResponse:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Missing artefact: {path}")
    return StreamingResponse(
        iter([_read_csv_bytes(path)]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/cost-analysis.csv", summary="Precomputed per-threshold sweep for one model")
def export_cost_analysis(model: str = Query(...)):
    return _stream_file(
        _tables_dir() / f"cost_analysis_{model}.csv",
        f"cost_analysis_{model}.csv",
    )


@router.get("/threshold-optimization.csv", summary="Key threshold optima for one model")
def export_threshold_optimization(model: str = Query(...)):
    return _stream_file(
        _tables_dir() / f"threshold_optimization_{model}.csv",
        f"threshold_optimization_{model}.csv",
    )


@router.get("/cost-comparison-summary.csv", summary="All models / all strategies")
def export_cost_comparison():
    return _stream_file(
        _tables_dir() / "cost_comparison_summary.csv",
        "cost_comparison_summary.csv",
    )


@router.get("/model-benchmark.csv", summary="Model benchmark table from run_evaluation.py")
def export_model_benchmark():
    return _stream_file(
        _tables_dir() / "model_comparison.csv",
        "model_benchmark_results.csv",
    )


# ----------------------------------------------------------------------
# Power BI bundle — single zip containing every CSV above
# ----------------------------------------------------------------------
def _csv_bytes(rows: Iterable[dict], columns: List[str]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe = {
            k: (json.dumps(v, default=str) if isinstance(v, (list, dict)) else v)
            for k, v in row.items()
            if k in columns
        }
        writer.writerow(safe)
    return buf.getvalue().encode("utf-8")


def _bundle_entries(db: Session) -> List[Tuple[str, bytes]]:
    """Return (filename, bytes) tuples for the Power BI zip."""
    entries: List[Tuple[str, bytes]] = []

    tx_rows = db.query(BankingTransaction).order_by(desc(BankingTransaction.created_at)).limit(50000).all()
    entries.append(("transactions_simulated.csv", _csv_bytes(map(_serialize_tx_row, tx_rows), TX_COLUMNS)))

    alert_rows = db.query(BankingAlert).order_by(desc(BankingAlert.created_at)).limit(50000).all()
    entries.append(("fraud_alerts.csv", _csv_bytes(map(_serialize_alert_row, alert_rows), ALERT_COLUMNS)))

    shap_rows = db.query(ShapExplanationRecord).order_by(desc(ShapExplanationRecord.created_at)).limit(50000).all()
    entries.append(("shap_summary.csv", _csv_bytes(map(_serialize_shap_row, shap_rows), SHAP_COLUMNS)))

    customer_rows = db.query(BankingCustomer).limit(50000).all()
    entries.append(("customers.csv", _csv_bytes(map(_serialize_customer_row, customer_rows), CUSTOMER_COLUMNS)))

    base = _tables_dir()
    if base.exists():
        for path in sorted(base.glob("*.csv")):
            entries.append((path.name, path.read_bytes()))

    # An always-present README explaining the bundle.
    readme = (
        "Power BI export bundle\n"
        "======================\n"
        f"Generated at: {datetime.utcnow().isoformat()}Z\n\n"
        "Live tables (populated by the simulator):\n"
        "  - transactions_simulated.csv\n"
        "  - fraud_alerts.csv\n"
        "  - shap_summary.csv\n"
        "  - customers.csv\n\n"
        "Precomputed thesis artefacts (from scripts/run_cost_analysis.py +\n"
        "scripts/run_evaluation.py):\n"
        "  - cost_analysis_{model}.csv\n"
        "  - threshold_optimization_{model}.csv\n"
        "  - cost_comparison_summary.csv\n"
        "  - model_comparison.csv\n\n"
        "Import into Power BI via 'Get Data' -> 'Folder' or one CSV at a time.\n"
    )
    entries.append(("README.txt", readme.encode("utf-8")))
    return entries


@router.get("/powerbi.zip", summary="Power BI export bundle (all CSVs in one zip)")
def export_powerbi_zip(db: Session = Depends(get_session)) -> Response:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, data in _bundle_entries(db):
            zf.writestr(filename, data)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="powerbi_bundle_{_stamp()}.zip"',
        },
    )


# ----------------------------------------------------------------------
# Simulation summary — single-row CSV for thesis tables
# ----------------------------------------------------------------------
@router.get("/simulation-summary.csv", summary="One-row summary of the live simulation")
def export_simulation_summary(db: Session = Depends(get_session)):
    total_tx = db.query(BankingTransaction).count()
    total_blocked = db.query(BankingTransaction).filter(BankingTransaction.decision == "BLOCKED").count()
    total_suspicious = db.query(BankingTransaction).filter(
        BankingTransaction.decision.in_(["SUSPICIOUS", "REVIEW"])
    ).count()
    total_approved = db.query(BankingTransaction).filter(BankingTransaction.decision == "APPROVED").count()

    real_fraud = db.query(BankingTransaction).filter(BankingTransaction.scenario != "normal").count()
    detected_fraud = db.query(BankingTransaction).filter(
        BankingTransaction.scenario != "normal",
        BankingTransaction.decision == "BLOCKED",
    ).count()
    missed_fraud = max(real_fraud - detected_fraud, 0)
    false_positives = db.query(BankingTransaction).filter(
        BankingTransaction.scenario == "normal",
        BankingTransaction.decision == "BLOCKED",
    ).count()
    avoided_loss = float(
        sum(
            ((row[0] if row[0] is not None else row[1]) or 0.0)
            for row in db.query(BankingTransaction.amount, BankingTransaction.transaction_amount)
            .filter(
                BankingTransaction.scenario != "normal",
                BankingTransaction.decision == "BLOCKED",
            )
            .all()
        )
    )

    detection_rate = (detected_fraud / real_fraud) if real_fraud else 0.0
    fp_rate = (false_positives / max(1, total_tx - real_fraud))

    row = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_transactions": total_tx,
        "approved": total_approved,
        "suspicious": total_suspicious,
        "blocked": total_blocked,
        "real_fraud_simulated": real_fraud,
        "detected_fraud": detected_fraud,
        "missed_fraud": missed_fraud,
        "false_positives": false_positives,
        "detection_rate": round(detection_rate, 4),
        "false_positive_rate": round(fp_rate, 4),
        "estimated_avoided_loss": round(avoided_loss, 2),
    }
    return _csv_response(
        [row],
        list(row.keys()),
        f"simulation_summary_{_stamp()}.csv",
    )


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S")
