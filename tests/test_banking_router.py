"""Smoke tests for the banking platform layer.

Covers:
- Pydantic schemas validate a real TransactionGenerator dict.
- BankingCustomer/BankingTransaction/BankingAlert ORM round-trip.
- record_banking_assessment + get_shap_explanation roundtrip.
- banking_analytics aggregates from an empty + populated DB.
- /api/v1/banking/simulator/status responds via TestClient.

Tests use an isolated in-memory SQLite engine bound to the global Base
metadata, so they neither touch nor depend on the dev fraud_detection.db.
"""
from __future__ import annotations

import os

# Force an isolated in-memory DB before any app/db modules are imported.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.schemas import BankingTransactionIn, SimulatorStatusOut
from src.database import crud
from src.database.session import Base
from src.scoring.dynamic_engine import DynamicFraudScoringEngine
from src.simulation.customers import CustomerGenerator
from src.simulation.transactions import TransactionGenerator


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _sample_transaction() -> dict:
    customers = CustomerGenerator(seed=7).generate_many(20)
    return TransactionGenerator(seed=7, customers=customers).generate_transaction(
        rate_tps=10, fraud_ratio=0.5, scenario="impossible_travel"
    )


def test_schema_accepts_generator_transaction():
    tx = _sample_transaction()
    parsed = BankingTransactionIn.model_validate(tx)
    assert parsed.transaction_id == tx["transaction_id"]
    assert parsed.transaction_amount == pytest.approx(tx["transaction_amount"])
    assert parsed.scenario == "impossible_travel"


def test_record_banking_assessment_roundtrip(db):
    tx = _sample_transaction()
    assessment = DynamicFraudScoringEngine().score(tx).as_dict()

    persisted = crud.record_banking_assessment(db, tx, assessment)

    assert persisted["score"].transaction_id == tx["transaction_id"]
    assert persisted["score"].model_version == assessment["model_version"]
    # impossible_travel is forced fraud — should trip the alert path.
    assert persisted["alert"] is not None
    assert persisted["shap"].transaction_id == tx["transaction_id"]

    fetched = crud.get_shap_explanation(db, tx["transaction_id"])
    assert fetched is not None
    assert fetched.top_reasons == assessment["top_reasons"]


def test_bulk_upsert_customers_and_list(db):
    customers = CustomerGenerator(seed=3).generate_many(5)
    inserted = crud.bulk_upsert_customers(db, customers)
    assert inserted == 5

    # Upserting the same set should not duplicate rows.
    crud.bulk_upsert_customers(db, customers)
    rows = crud.list_customers(db, limit=100)
    assert len(rows) == 5


def test_banking_analytics_empty_and_populated(db):
    empty = crud.banking_analytics(db)
    assert empty["total_transactions"] == 0
    assert empty["fraud_rate"] == 0.0

    engine = DynamicFraudScoringEngine()
    gen = TransactionGenerator(seed=11, customers=CustomerGenerator(seed=11).generate_many(50))
    for _ in range(15):
        tx = gen.generate_transaction(rate_tps=10, fraud_ratio=0.6)
        crud.record_banking_assessment(db, tx, engine.score(tx).as_dict())

    populated = crud.banking_analytics(db)
    assert populated["total_transactions"] == 15
    assert populated["approved"] + populated["suspicious"] + populated["blocked"] == 15
    assert isinstance(populated["top_countries"], list)
    assert populated["total_amount"] > 0


def test_banking_simulator_status_endpoint_via_client():
    # Local import so the DATABASE_URL env override above is in effect.
    from src.api.main import app

    client = TestClient(app)
    response = client.get("/api/v1/banking/simulator/status")
    assert response.status_code == 200
    SimulatorStatusOut.model_validate(response.json())
