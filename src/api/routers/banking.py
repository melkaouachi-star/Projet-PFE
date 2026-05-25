"""Enterprise banking fraud-platform endpoints."""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.api.dependencies import get_session
from src.api.schemas import (
    BankingAlertRecord,
    BankingAnalyticsOut,
    BankingCustomerOut,
    BankingDecisionOut,
    BankingShapExplanationOut,
    BankingTransactionIn,
    BankingTransactionRecord,
    GenerateCustomersIn,
    SimulatorControlIn,
    SimulatorStatusOut,
)
from src.database import crud
from src.scoring.dynamic_engine import assessment_dict, assessment_to_event
from src.simulation.customers import CustomerGenerator
from src.streaming.broker import get_broker, sse_pack
from src.streaming.simulator import get_simulation_service

router = APIRouter(tags=["enterprise-banking-platform"])


@router.post("/predict", response_model=BankingDecisionOut, summary="Score a realistic banking transaction")
@router.post("/api/v1/banking/predict", response_model=BankingDecisionOut, include_in_schema=False)
async def predict_banking_transaction(
    payload: BankingTransactionIn,
    db: Session = Depends(get_session),
) -> BankingDecisionOut:
    transaction = payload.model_dump()
    service = get_simulation_service()
    assessment = service.engine.score(transaction)
    persisted = crud.record_banking_assessment(db, transaction, assessment.as_dict())
    event = assessment_to_event(transaction, assessment)
    await get_broker().publish(event)
    return _decision_out(transaction, assessment_dict(transaction, assessment), persisted["score"].model_version)


@router.get("/transactions", response_model=List[BankingTransactionRecord], summary="Recent live banking transactions")
@router.get("/api/v1/banking/transactions", response_model=List[BankingTransactionRecord], include_in_schema=False)
def recent_banking_transactions(
    limit: int = Query(100, ge=1, le=2000),
    db: Session = Depends(get_session),
):
    return crud.list_recent_banking_transactions(db, limit=limit)


@router.post("/customers/generate", summary="Generate synthetic banking customers")
@router.post("/api/v1/banking/customers/generate", include_in_schema=False)
def generate_customers(
    payload: GenerateCustomersIn,
    db: Session = Depends(get_session),
):
    customers = CustomerGenerator(seed=payload.seed).generate_many(payload.count)
    if payload.persist:
        crud.bulk_upsert_customers(db, customers)
    get_simulation_service().configure_customers(customers)
    return {
        "generated": len(customers),
        "persisted": payload.persist,
        "sample": customers[:5],
    }


@router.get("/customers", response_model=List[BankingCustomerOut], summary="Synthetic customer profiles")
@router.get("/api/v1/banking/customers", response_model=List[BankingCustomerOut], include_in_schema=False)
def customers(
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    return crud.list_customers(db, limit=limit, offset=offset)


@router.get("/fraud-alerts", response_model=List[BankingAlertRecord], summary="Real-time fraud alerts")
@router.get("/api/v1/banking/fraud-alerts", response_model=List[BankingAlertRecord], include_in_schema=False)
def fraud_alerts(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_session),
):
    return crud.list_recent_banking_alerts(db, limit=limit)


@router.get("/analytics/live", response_model=BankingAnalyticsOut, summary="Live fraud analytics")
@router.get("/api/v1/banking/analytics/live", response_model=BankingAnalyticsOut, include_in_schema=False)
def live_analytics(db: Session = Depends(get_session)):
    return crud.banking_analytics(db)


@router.get("/shap-explanation", response_model=BankingShapExplanationOut, summary="SHAP-style explanation for a transaction")
@router.get("/api/v1/banking/shap-explanation", response_model=BankingShapExplanationOut, include_in_schema=False)
def shap_explanation(
    transaction_id: str = Query(...),
    db: Session = Depends(get_session),
):
    exp = crud.get_shap_explanation(db, transaction_id)
    if exp is None:
        return BankingShapExplanationOut(
            transaction_id=transaction_id,
            base_value=0.0,
            feature_names=[],
            shap_values=[],
            top_reasons=["No explanation was found for this transaction."],
            risk_contribution_score={},
        )
    return BankingShapExplanationOut(
        transaction_id=transaction_id,
        base_value=exp.base_value,
        feature_names=exp.feature_names,
        shap_values=exp.shap_values,
        top_reasons=exp.top_reasons,
        risk_contribution_score=exp.risk_contribution_score,
    )


@router.post("/simulator/start", response_model=SimulatorStatusOut, summary="Start fraud simulator")
@router.post("/api/v1/banking/simulator/start", response_model=SimulatorStatusOut, include_in_schema=False)
async def start_simulator(payload: SimulatorControlIn):
    return await get_simulation_service().start(
        rate_tps=payload.rate_tps,
        fraud_ratio=payload.fraud_ratio,
    )


@router.post("/simulator/stop", response_model=SimulatorStatusOut, summary="Stop fraud simulator")
@router.post("/api/v1/banking/simulator/stop", response_model=SimulatorStatusOut, include_in_schema=False)
async def stop_simulator():
    return await get_simulation_service().stop()


@router.get("/simulator/status", response_model=SimulatorStatusOut, summary="Simulator status")
@router.get("/api/v1/banking/simulator/status", response_model=SimulatorStatusOut, include_in_schema=False)
def simulator_status():
    return get_simulation_service().status()


@router.get("/simulator/sample", summary="Generate one synthetic transaction without persisting it")
@router.get("/api/v1/banking/simulator/sample", include_in_schema=False)
def simulator_sample(
    scenario: str | None = Query(None),
    rate_tps: int = Query(10),
    fraud_ratio: float = Query(0.08, ge=0.0, le=1.0),
):
    return get_simulation_service().generator.generate_transaction(
        rate_tps=rate_tps,
        fraud_ratio=fraud_ratio,
        scenario=scenario,
    )


@router.get("/live-stream", summary="Server-Sent Events transaction stream")
@router.get("/api/v1/banking/live-stream", include_in_schema=False)
async def live_stream():
    async def event_generator():
        async with get_broker().subscribe(replay=25) as queue:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                    yield sse_pack(event)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.websocket("/ws/live-stream")
@router.websocket("/api/v1/banking/ws/live-stream")
async def websocket_live_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        async with get_broker().subscribe(replay=25) as queue:
            while True:
                event = await queue.get()
                await websocket.send_json(event)
    except WebSocketDisconnect:
        return


def _decision_out(transaction: dict, detail: dict, model_version: str) -> BankingDecisionOut:
    return BankingDecisionOut(
        transaction_id=transaction["transaction_id"],
        customer_id=transaction["customer_id"],
        customer_name=transaction["customer_name"],
        timestamp=transaction["timestamp"],
        country=transaction["country"],
        city=transaction["city"],
        latitude=transaction["latitude"],
        longitude=transaction["longitude"],
        ip_address=transaction["ip_address"],
        amount=transaction["transaction_amount"],
        currency=transaction["transaction_currency"],
        merchant_name=transaction["merchant_name"],
        merchant_category=transaction["merchant_category"],
        fraud_probability=detail["fraud_probability"],
        risk_score=detail["risk_score"],
        fraud_level=detail["fraud_level"],
        decision=detail["decision"],
        transaction_status=detail["transaction_status"],
        threshold=detail["threshold"],
        model_version=model_version,
        top_reasons=detail["top_reasons"],
        contributions=[asdict(c) if not isinstance(c, dict) else c for c in detail["contributions"]],
    )

