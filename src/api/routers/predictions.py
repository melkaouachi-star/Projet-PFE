"""Prediction & decision endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.decision_engine import FraudDecisionEngine
from src.api.dependencies import engine_dep, get_session
from src.api.schemas import BatchIn, DecisionOut, TransactionIn
from src.database import crud
from src.utils.logger import get_logger

router = APIRouter(prefix="/api/v1", tags=["predictions"])
log = get_logger("api.predictions")


@router.post("/predict", response_model=DecisionOut, summary="Score a transaction in real time")
def predict_transaction(
    payload: TransactionIn,
    engine: FraudDecisionEngine = Depends(engine_dep),
    db: Session = Depends(get_session),
) -> DecisionOut:
    """
    Receive a single transaction, score it, persist the result and
    return a structured banking-grade decision.
    """
    raw = payload.to_dict_no_meta()
    try:
        decision = engine.score(raw)
    except Exception as exc:
        log.exception(f"Scoring failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {exc}") from exc

    tx = crud.create_transaction(db, raw, external_id=payload.external_id)
    pred = crud.create_prediction(
        db,
        transaction_id=tx.id,
        model_name=decision.model_name,
        probability=decision.fraud_probability,
        risk_score=decision.risk_score,
        threshold=decision.threshold,
        decision=decision.decision,
        explanation=decision.explanation,
    )
    if decision.decision.value in ("BLOCKED", "REVIEW"):
        crud.create_alert(
            db,
            transaction_id=tx.id,
            prediction_id=pred.id,
            severity="HIGH" if decision.decision.value == "BLOCKED" else "MEDIUM",
            message=f"{decision.decision.value} transaction "
                    f"(amount={raw.get('Amount',0):.2f}, p={decision.fraud_probability:.3f})",
        )

    return DecisionOut(
        transaction_id=tx.id,
        fraud_probability=round(decision.fraud_probability, 6),
        risk_score=decision.risk_score,
        decision=decision.decision.value,
        threshold=decision.threshold,
        explanation=decision.explanation,
        model_name=decision.model_name,
        created_at=pred.created_at,
    )


@router.post("/predict/batch", response_model=List[DecisionOut], summary="Score many transactions")
def predict_batch(
    batch: BatchIn,
    engine: FraudDecisionEngine = Depends(engine_dep),
    db: Session = Depends(get_session),
) -> List[DecisionOut]:
    out: List[DecisionOut] = []
    for tx in batch.transactions:
        out.append(predict_transaction(tx, engine=engine, db=db))
    return out
