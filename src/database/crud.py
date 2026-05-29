"""CRUD helpers - keep API routes free of raw SQLAlchemy noise."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.database.models import (
    BankingAlert,
    BankingCustomer,
    BankingTransaction,
    Decision,
    FraudAlert,
    Prediction,
    ShapExplanationRecord,
    SimulationRun,
    Transaction,
)


def create_transaction(db: Session, payload: dict, external_id: Optional[str] = None) -> Transaction:
    tx = Transaction(
        external_id=external_id,
        time_seconds=float(payload.get("Time", 0.0)),
        amount=float(payload.get("Amount", 0.0)),
        raw_payload=payload,
    )
    db.add(tx); db.commit(); db.refresh(tx)
    return tx


def create_prediction(db: Session, *, transaction_id: int, model_name: str,
                      probability: float, risk_score: int, threshold: float,
                      decision: Decision, explanation: list[str] | None) -> Prediction:
    pred = Prediction(
        transaction_id=transaction_id,
        model_name=model_name,
        fraud_probability=probability,
        risk_score=risk_score,
        threshold=threshold,
        decision=decision,
        explanation=explanation,
    )
    db.add(pred); db.commit(); db.refresh(pred)
    return pred


def create_alert(db: Session, *, transaction_id: int, prediction_id: int,
                 severity: str, message: str) -> FraudAlert:
    alert = FraudAlert(
        transaction_id=transaction_id,
        prediction_id=prediction_id,
        severity=severity,
        message=message,
    )
    db.add(alert); db.commit(); db.refresh(alert)
    return alert


def list_recent_predictions(db: Session, limit: int = 100) -> List[Prediction]:
    return db.query(Prediction).order_by(desc(Prediction.created_at)).limit(limit).all()


def list_recent_alerts(db: Session, limit: int = 100) -> List[FraudAlert]:
    return db.query(FraudAlert).order_by(desc(FraudAlert.created_at)).limit(limit).all()


def stats_summary(db: Session) -> dict:
    """High-level counters for the dashboard."""
    n_tx = db.query(Transaction).count()
    n_pred = db.query(Prediction).count()
    n_blocked = db.query(Prediction).filter(Prediction.decision == Decision.BLOCKED).count()
    n_review = db.query(Prediction).filter(Prediction.decision == Decision.REVIEW).count()
    n_alerts = db.query(FraudAlert).count()
    return {
        "transactions": n_tx,
        "predictions": n_pred,
        "blocked": n_blocked,
        "review": n_review,
        "alerts": n_alerts,
    }


# ======================================================================
# Banking-platform CRUD
#
# Used by src/api/routers/banking.py and src/streaming/simulator.py.
# Returns plain ORM rows (Pydantic schemas with from_attributes=True will
# coerce them) or plain dicts for analytics.  Each function is isolated:
# they do NOT touch the legacy Transaction / Prediction / FraudAlert
# tables above.
# ======================================================================


def _coerce_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def bulk_upsert_customers(db: Session, customers: Iterable[dict]) -> int:
    """Insert-or-update synthetic customers by primary key."""
    n = 0
    for c in customers:
        cid = c.get("customer_id")
        if not cid:
            continue
        existing = db.get(BankingCustomer, cid)
        payload = dict(
            full_name=c.get("full_name"),
            age=c.get("age"),
            country=c.get("country"),
            city=c.get("city"),
            latitude=c.get("latitude"),
            longitude=c.get("longitude"),
            account_age_days=c.get("account_age_days"),
            average_spending=c.get("average_spending"),
            risk_profile=c.get("risk_profile"),
            behavior_pattern=c.get("behavior_pattern"),
            known_devices=c.get("known_devices"),
            usual_countries=c.get("usual_countries"),
            fraud_history_count=c.get("fraud_history_count", 0),
            updated_at=datetime.utcnow(),
        )
        if existing is None:
            db.add(BankingCustomer(customer_id=cid, **payload))
        else:
            for k, v in payload.items():
                setattr(existing, k, v)
        n += 1
    db.commit()
    return n


def list_customers(db: Session, limit: int = 100, offset: int = 0) -> List[BankingCustomer]:
    return (
        db.query(BankingCustomer)
        .order_by(desc(BankingCustomer.updated_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


def record_banking_assessment(
    db: Session, transaction: dict, assessment: dict, simulation_run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Persist one (transaction, score) pair.

    - Upserts the BankingTransaction row keyed by transaction_id.
    - Creates a BankingAlert row when the decision is BLOCKED / SUSPICIOUS.
    - Upserts the SHAP explanation keyed by transaction_id.

    Returns ``{"score": BankingTransaction, "alert": BankingAlert|None,
              "shap": ShapExplanationRecord}`` — the banking router reads
    ``persisted["score"].model_version`` from this payload.
    """
    tid = str(transaction.get("transaction_id"))
    ts = _coerce_timestamp(transaction.get("timestamp"))
    amount = float(transaction.get("transaction_amount", transaction.get("amount", 0.0)))
    currency = transaction.get("transaction_currency") or transaction.get("currency") or "USD"

    payload = dict(
        customer_id=str(transaction.get("customer_id", "")),
        simulation_run_id=simulation_run_id,
        customer_name=transaction.get("customer_name"),
        customer_age=transaction.get("customer_age"),
        customer_risk_category=transaction.get("customer_risk_category"),
        timestamp=ts,
        country=transaction.get("country"),
        city=transaction.get("city"),
        latitude=transaction.get("latitude"),
        longitude=transaction.get("longitude"),
        ip_address=transaction.get("ip_address"),
        device_id=transaction.get("device_id"),
        browser=transaction.get("browser"),
        operating_system=transaction.get("operating_system"),
        amount=amount,
        currency=currency,
        transaction_amount=amount,
        transaction_currency=currency,
        transaction_date=transaction.get("transaction_date"),
        transaction_time=transaction.get("transaction_time"),
        merchant_name=transaction.get("merchant_name"),
        merchant_category=transaction.get("merchant_category"),
        payment_method=transaction.get("payment_method"),
        card_type=transaction.get("card_type"),
        scenario=transaction.get("scenario"),
        fraud_probability=float(assessment.get("fraud_probability", 0.0)),
        risk_score=int(assessment.get("risk_score", 0)),
        fraud_level=assessment.get("fraud_level"),
        decision=assessment.get("decision"),
        transaction_status=assessment.get("transaction_status"),
        model_version=assessment.get("model_version"),
        raw_payload={"transaction": _jsonable(transaction), "assessment": _jsonable(assessment)},
    )

    score_row = db.get(BankingTransaction, tid)
    if score_row is None:
        score_row = BankingTransaction(transaction_id=tid, **payload)
        db.add(score_row)
    else:
        for k, v in payload.items():
            setattr(score_row, k, v)

    alert_row: Optional[BankingAlert] = None
    decision = (assessment.get("decision") or "").upper()
    if decision in {"BLOCKED", "SUSPICIOUS", "REVIEW"}:
        alert_row = BankingAlert(
            transaction_id=tid,
            customer_id=str(transaction.get("customer_id", "")),
            customer_name=transaction.get("customer_name"),
            severity=assessment.get("alert_severity") or ("HIGH" if decision == "BLOCKED" else "MEDIUM"),
            fraud_level=assessment.get("fraud_level"),
            risk_score=int(assessment.get("risk_score", 0)),
            fraud_probability=float(assessment.get("fraud_probability", 0.0)),
            decision=assessment.get("decision"),
            amount=amount,
            currency=currency,
            country=transaction.get("country"),
            city=transaction.get("city"),
            ip_address=transaction.get("ip_address"),
            message=assessment.get("alert_message") or f"{decision} transaction {tid}",
            top_reasons=assessment.get("top_reasons") or [],
        )
        db.add(alert_row)

    shap_row = db.get(ShapExplanationRecord, tid)
    shap_payload = dict(
        base_value=float(assessment.get("base_value", 0.0)),
        feature_names=list(assessment.get("feature_names") or []),
        shap_values=list(assessment.get("shap_values") or []),
        top_reasons=list(assessment.get("top_reasons") or []),
        risk_contribution_score=_jsonable(assessment.get("risk_contribution_score") or {}),
    )
    if shap_row is None:
        shap_row = ShapExplanationRecord(transaction_id=tid, **shap_payload)
        db.add(shap_row)
    else:
        for k, v in shap_payload.items():
            setattr(shap_row, k, v)

    db.commit()
    db.refresh(score_row)
    if alert_row is not None:
        db.refresh(alert_row)
    db.refresh(shap_row)
    return {"score": score_row, "alert": alert_row, "shap": shap_row}


def list_recent_banking_transactions(db: Session, limit: int = 100) -> List[dict]:
    rows = (
        db.query(BankingTransaction)
        .order_by(desc(BankingTransaction.created_at))
        .limit(limit)
        .all()
    )
    return [_serialize_banking_transaction(row) for row in rows]


def list_recent_banking_alerts(db: Session, limit: int = 100) -> List[BankingAlert]:
    return (
        db.query(BankingAlert)
        .order_by(desc(BankingAlert.created_at))
        .limit(limit)
        .all()
    )


def get_shap_explanation(db: Session, transaction_id: str) -> Optional[ShapExplanationRecord]:
    return db.get(ShapExplanationRecord, str(transaction_id))


def banking_analytics(db: Session) -> Dict[str, Any]:
    """Live aggregates for the analytics endpoint."""
    total_tx = db.query(BankingTransaction).count()
    if total_tx == 0:
        return {
            "total_transactions": 0,
            "total_amount": 0.0,
            "approved": 0,
            "suspicious": 0,
            "blocked": 0,
            "fraud_rate": 0.0,
            "avg_risk_score": 0.0,
            "high_risk_alerts": 0,
            "estimated_avoided_loss": 0.0,
            "top_countries": [],
            "top_merchant_categories": [],
            "scenarios": [],
        }

    decision_counts = dict(
        db.query(BankingTransaction.decision, func.count(BankingTransaction.transaction_id))
        .group_by(BankingTransaction.decision)
        .all()
    )
    blocked = int(decision_counts.get("BLOCKED", 0))
    suspicious = int(decision_counts.get("SUSPICIOUS", 0)) + int(decision_counts.get("REVIEW", 0))
    approved = int(decision_counts.get("APPROVED", 0))

    amount_expr = func.coalesce(BankingTransaction.amount, BankingTransaction.transaction_amount, 0.0)
    total_amount = float(db.query(func.coalesce(func.sum(amount_expr), 0.0)).scalar() or 0.0)
    avg_risk = float(db.query(func.coalesce(func.avg(BankingTransaction.risk_score), 0.0)).scalar() or 0.0)
    blocked_amount = float(
        db.query(func.coalesce(func.sum(amount_expr), 0.0))
        .filter(BankingTransaction.decision == "BLOCKED")
        .scalar()
        or 0.0
    )
    high_risk_alerts = (
        db.query(BankingAlert).filter(BankingAlert.severity.in_(["HIGH", "CRITICAL"])).count()
    )

    top_countries = [
        {"country": c or "Unknown", "count": int(n)}
        for c, n in db.query(BankingTransaction.country, func.count(BankingTransaction.transaction_id))
        .group_by(BankingTransaction.country)
        .order_by(desc(func.count(BankingTransaction.transaction_id)))
        .limit(10)
        .all()
    ]
    top_categories = [
        {"category": c or "Unknown", "count": int(n)}
        for c, n in db.query(BankingTransaction.merchant_category, func.count(BankingTransaction.transaction_id))
        .group_by(BankingTransaction.merchant_category)
        .order_by(desc(func.count(BankingTransaction.transaction_id)))
        .limit(10)
        .all()
    ]
    scenarios = [
        {"scenario": s or "unknown", "count": int(n)}
        for s, n in db.query(BankingTransaction.scenario, func.count(BankingTransaction.transaction_id))
        .group_by(BankingTransaction.scenario)
        .order_by(desc(func.count(BankingTransaction.transaction_id)))
        .all()
    ]

    return {
        "total_transactions": int(total_tx),
        "total_amount": round(total_amount, 2),
        "approved": approved,
        "suspicious": suspicious,
        "blocked": blocked,
        "fraud_rate": round((blocked + suspicious) / max(1, total_tx), 4),
        "avg_risk_score": round(avg_risk, 2),
        "high_risk_alerts": int(high_risk_alerts),
        "estimated_avoided_loss": round(blocked_amount, 2),
        "top_countries": top_countries,
        "top_merchant_categories": top_categories,
        "scenarios": scenarios,
    }


def _jsonable(value: Any) -> Any:
    """Coerce values to something the SQLAlchemy JSON column can store."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


# ======================================================================
# Simulation-run lifecycle (Power BI dim_simulation_run)
# ======================================================================
def create_simulation_run(
    db: Session,
    *,
    run_id: str,
    rate_tps: int,
    fraud_ratio: float,
    model_version: Optional[str] = None,
) -> SimulationRun:
    """Open a new ACTIVE simulation run row."""
    run = SimulationRun(
        run_id=run_id,
        started_at=datetime.utcnow(),
        status="ACTIVE",
        rate_tps=int(rate_tps),
        fraud_ratio=float(fraud_ratio),
        model_version=model_version,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finalize_simulation_run(db: Session, run_id: str) -> Optional[SimulationRun]:
    """Close a run and snapshot its aggregate effectiveness metrics.

    Aggregates are recomputed from ``banking_transactions`` filtered by
    ``simulation_run_id`` so the snapshot always matches the persisted rows
    (no double counting, no dependence on in-memory counters).
    """
    run = db.get(SimulationRun, run_id)
    if run is None:
        return None

    base = db.query(BankingTransaction).filter(
        BankingTransaction.simulation_run_id == run_id
    )
    total = base.count()
    decision_counts = dict(
        db.query(BankingTransaction.decision, func.count(BankingTransaction.transaction_id))
        .filter(BankingTransaction.simulation_run_id == run_id)
        .group_by(BankingTransaction.decision)
        .all()
    )
    blocked = int(decision_counts.get("BLOCKED", 0))
    suspicious = int(decision_counts.get("SUSPICIOUS", 0)) + int(decision_counts.get("REVIEW", 0))
    approved = int(decision_counts.get("APPROVED", 0))

    simulated_frauds = base.filter(BankingTransaction.scenario != "normal").count()
    detected_frauds = base.filter(
        BankingTransaction.scenario != "normal", BankingTransaction.decision == "BLOCKED"
    ).count()
    false_positives = base.filter(
        BankingTransaction.scenario == "normal", BankingTransaction.decision == "BLOCKED"
    ).count()
    amount_expr = func.coalesce(BankingTransaction.amount, BankingTransaction.transaction_amount, 0.0)
    avoided_loss = float(
        db.query(func.coalesce(func.sum(amount_expr), 0.0))
        .filter(
            BankingTransaction.simulation_run_id == run_id,
            BankingTransaction.scenario != "normal",
            BankingTransaction.decision == "BLOCKED",
        )
        .scalar()
        or 0.0
    )

    run.stopped_at = datetime.utcnow()
    run.status = "COMPLETED"
    run.generated_transactions = total
    run.approved = approved
    run.suspicious = suspicious
    run.blocked = blocked
    run.simulated_frauds = simulated_frauds
    run.detected_frauds = detected_frauds
    run.missed_frauds = max(simulated_frauds - detected_frauds, 0)
    run.false_positives = false_positives
    run.estimated_avoided_loss = round(avoided_loss, 2)
    db.commit()
    db.refresh(run)
    return run


def list_simulation_runs(db: Session, limit: int = 100) -> List[SimulationRun]:
    return (
        db.query(SimulationRun)
        .order_by(desc(SimulationRun.started_at))
        .limit(limit)
        .all()
    )


def _serialize_banking_transaction(row: BankingTransaction) -> dict:
    amount = row.amount if row.amount is not None else (row.transaction_amount or 0.0)
    currency = row.currency or row.transaction_currency or "USD"
    return {
        "transaction_id": row.transaction_id,
        "customer_id": row.customer_id,
        "customer_name": row.customer_name,
        "timestamp": row.timestamp,
        "country": row.country,
        "city": row.city,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "ip_address": row.ip_address,
        "amount": float(amount or 0.0),
        "currency": currency,
        "merchant_name": row.merchant_name,
        "merchant_category": row.merchant_category,
        "scenario": row.scenario,
        "fraud_probability": row.fraud_probability,
        "risk_score": row.risk_score,
        "fraud_level": row.fraud_level,
        "decision": row.decision,
        "transaction_status": row.transaction_status,
        "model_version": row.model_version,
        "created_at": row.created_at,
    }
