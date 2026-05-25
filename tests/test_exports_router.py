"""Tests for the Phase 3 export endpoints (CSV + Power BI ZIP)."""
from __future__ import annotations

import csv
import io
import os
import zipfile

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.database import crud
from src.database.session import Base, SessionLocal, engine
from src.scoring.dynamic_engine import DynamicFraudScoringEngine
from src.simulation.customers import CustomerGenerator
from src.simulation.transactions import TransactionGenerator


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def populated_db():
    customers = CustomerGenerator(seed=42).generate_many(20)
    eng = DynamicFraudScoringEngine()
    gen = TransactionGenerator(seed=42, customers=customers)
    with SessionLocal() as db:
        crud.bulk_upsert_customers(db, customers)
        for _ in range(60):
            tx = gen.generate_transaction(rate_tps=10, fraud_ratio=0.5)
            crud.record_banking_assessment(db, tx, eng.score(tx).as_dict())


@pytest.fixture()
def client():
    return TestClient(app)


def _csv_header(body: bytes) -> list[str]:
    return next(csv.reader(io.StringIO(body.decode("utf-8"))))


def test_inventory_lists_endpoints(client):
    resp = client.get("/api/v1/export/inventory")
    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()["items"]}
    assert {"banking_transactions", "banking_fraud_alerts", "powerbi_bundle"}.issubset(names)


def test_transactions_csv_has_expected_header(client, populated_db):
    resp = client.get("/api/v1/export/transactions.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    header = _csv_header(resp.content)
    for col in ("transaction_id", "customer_id", "amount", "currency",
                "fraud_probability", "risk_score", "decision", "scenario"):
        assert col in header
    # Header + N data rows.
    assert resp.content.decode("utf-8").count("\n") >= 2


def test_fraud_alerts_csv_only_for_blocked_or_suspicious(client, populated_db):
    resp = client.get("/api/v1/export/fraud-alerts.csv")
    assert resp.status_code == 200
    header = _csv_header(resp.content)
    assert "severity" in header and "top_reasons" in header


def test_shap_summary_csv_contains_json_columns(client, populated_db):
    resp = client.get("/api/v1/export/shap-summary.csv")
    assert resp.status_code == 200
    header = _csv_header(resp.content)
    for col in ("transaction_id", "feature_names", "shap_values", "risk_contribution_score"):
        assert col in header


def test_customers_csv(client, populated_db):
    resp = client.get("/api/v1/export/customers.csv")
    assert resp.status_code == 200
    header = _csv_header(resp.content)
    assert "customer_id" in header and "risk_profile" in header


def test_simulation_summary_single_row(client, populated_db):
    resp = client.get("/api/v1/export/simulation-summary.csv")
    assert resp.status_code == 200
    reader = list(csv.reader(io.StringIO(resp.content.decode("utf-8"))))
    assert len(reader) == 2  # header + 1 row
    body = dict(zip(reader[0], reader[1]))
    assert int(body["total_transactions"]) > 0
    assert int(body["real_fraud_simulated"]) >= 0


def test_powerbi_zip_bundle(client, populated_db):
    resp = client.get("/api/v1/export/powerbi.zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = set(zf.namelist())
        # Live entries should always be present.
        for required in (
            "transactions_simulated.csv",
            "fraud_alerts.csv",
            "shap_summary.csv",
            "customers.csv",
            "README.txt",
        ):
            assert required in names, (required, names)


def test_precomputed_csv_endpoints_missing(client):
    # No precomputed artefacts in this fresh worktree -> 404 for these.
    for url in (
        "/api/v1/export/cost-analysis.csv?model=nope",
        "/api/v1/export/threshold-optimization.csv?model=nope",
        "/api/v1/export/cost-comparison-summary.csv",
        "/api/v1/export/model-benchmark.csv",
    ):
        resp = client.get(url)
        assert resp.status_code == 404, url
