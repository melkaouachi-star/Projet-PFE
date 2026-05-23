"""CRUD helpers - keep API routes free of raw SQLAlchemy noise."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.database.models import Decision, FraudAlert, Prediction, Transaction


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
