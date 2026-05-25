"""Tests for the Phase 3 cost-analysis + optimal-threshold endpoints.

Coverage:
- POST /api/v1/cost-analysis/compute round-trips through the live banking
  table when populated by the simulator.
- Empty-database case returns 404 with a hint.
- /cost-analysis (offline) returns 404 when no precomputed CSV exists.
- /cost-analysis/models lists precomputed models.
"""
from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.database import crud
from src.database.session import Base, SessionLocal, engine
from src.evaluation.cost_analysis import CostParameters, run_full_analysis
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
    """Seed banking_transactions with a healthy mix of fraud + legit."""
    eng = DynamicFraudScoringEngine()
    customers = CustomerGenerator(seed=21).generate_many(40)
    gen = TransactionGenerator(seed=21, customers=customers)
    with SessionLocal() as db:
        for _ in range(120):
            tx = gen.generate_transaction(rate_tps=10, fraud_ratio=0.55)
            crud.record_banking_assessment(db, tx, eng.score(tx).as_dict())


@pytest.fixture()
def client():
    return TestClient(app)


def test_compute_endpoint_returns_sweep_and_optima(client, populated_db):
    resp = client.post(
        "/api/v1/cost-analysis/compute",
        json={"model_name": "live_test", "limit": 200, "mode": "fixed", "c_fn": 200, "c_fp": 10},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["model_name"] == "live_test"
    assert body["source"] == "live"
    assert body["mode"] == "fixed"
    assert isinstance(body["sweep"], list) and len(body["sweep"]) > 50
    for key in ("default", "f1", "mcc", "cost"):
        assert key in body["optima"]
    cost_opt = body["optima"]["cost"]
    default_opt = body["optima"]["default"]
    assert cost_opt["total_cost"] <= default_opt["total_cost"] + 1e-6


def test_compute_endpoint_empty_db_returns_404(client):
    resp = client.post("/api/v1/cost-analysis/compute", json={"limit": 100})
    assert resp.status_code == 404
    assert "simulator" in resp.json()["detail"].lower()


def test_offline_cost_analysis_missing_model_returns_404(client):
    resp = client.get("/api/v1/cost-analysis", params={"model": "this_model_does_not_exist"})
    assert resp.status_code == 404
    assert "run_cost_analysis" in resp.json()["detail"]


def test_offline_cost_analysis_roundtrip(client, tmp_path, monkeypatch):
    """Drop a synthetic precomputed CSV in tables_dir and read it back."""
    import numpy as np

    from src.api.routers import cost as cost_router

    # Force the router to look at our tmp tables dir.
    monkeypatch.setattr(cost_router, "_tables_dir", lambda: tmp_path)

    rng = np.random.default_rng(0)
    y = np.concatenate([np.zeros(800, int), np.ones(40, int)])
    p = np.concatenate([rng.beta(2, 8, 800), rng.beta(7, 2, 40)])
    rng.shuffle(p)
    rng.shuffle(y)

    result = run_full_analysis(
        y_true=y, y_proba=p,
        model_name="synthetic_demo",
        cost_params=CostParameters(mode="fixed", c_fn=100, c_fp=5),
        write_tables_dir=tmp_path,
        write_plots=False,
    )
    assert (tmp_path / "cost_analysis_synthetic_demo.csv").exists()

    resp = client.get("/api/v1/cost-analysis", params={"model": "synthetic_demo"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "offline"
    assert body["model_name"] == "synthetic_demo"
    assert len(body["sweep"]) > 50

    # /cost-analysis/models should now include the synthetic model.
    resp = client.get("/api/v1/cost-analysis/models")
    assert resp.status_code == 200
    assert "synthetic_demo" in resp.json()["models"]


def test_optimal_threshold_strategies(client, tmp_path, monkeypatch):
    import numpy as np

    from src.api.routers import cost as cost_router

    monkeypatch.setattr(cost_router, "_tables_dir", lambda: tmp_path)

    rng = np.random.default_rng(1)
    y = np.concatenate([np.zeros(500, int), np.ones(30, int)])
    p = np.concatenate([rng.beta(2, 8, 500), rng.beta(7, 2, 30)])
    rng.shuffle(p)
    rng.shuffle(y)
    run_full_analysis(
        y_true=y, y_proba=p,
        model_name="m1",
        cost_params=CostParameters(mode="fixed", c_fn=300, c_fp=10),
        write_tables_dir=tmp_path,
        write_plots=False,
    )

    for strategy in ("cost", "f1", "mcc", "default"):
        resp = client.get(
            "/api/v1/optimal-threshold",
            params={"model": "m1", "strategy": strategy},
        )
        assert resp.status_code == 200, (strategy, resp.text)
        body = resp.json()
        assert body["strategy"] == strategy
        assert 0.0 <= body["threshold"] <= 1.0

    bad = client.get("/api/v1/optimal-threshold", params={"model": "m1", "strategy": "invalid"})
    assert bad.status_code == 422  # FastAPI regex validation
