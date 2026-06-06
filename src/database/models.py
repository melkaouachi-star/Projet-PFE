"""ORM models for the fraud-detection platform."""
from __future__ import annotations

import enum
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    func,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.session import Base  # noqa: E402


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Decision(str, enum.Enum):
    APPROVED = "APPROVED"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class Transaction(Base):
    """A raw incoming transaction."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(64), index=True, nullable=True)
    time_seconds: Column[float] = Column(Float, nullable=False)
    amount: Column[float] = Column(Float, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    received_at = Column(DateTime, default=utc_now, nullable=False)


class Prediction(Base):
    """Output of the fraud-detection engine for one transaction."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, index=True, nullable=False)
    model_name = Column(String(64), nullable=False)
    fraud_probability: Column[float] = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    threshold: Column[float] = Column(Float, nullable=False)
    decision = Column(Enum(Decision), nullable=False)
    explanation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class FraudAlert(Base):
    """Alerts surfaced to the security analysts / customer."""
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, index=True, nullable=False)
    prediction_id = Column(Integer, index=True, nullable=False)
    severity = Column(String(16), nullable=False, default="HIGH")
    message = Column(Text, nullable=False)
    acknowledged = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


# ======================================================================
# Banking-platform tables
#
# Populated by the live banking simulator (src/streaming/simulator.py)
# and consumed by src/api/routers/banking.py + Power BI exports.
# Additive only — the original Transaction / Prediction / FraudAlert
# tables above are kept unchanged for backward compatibility with the
# /api/v1/predict, /predictions, /alerts and /stats endpoints.
# ======================================================================


class BankingCustomer(Base):
    """Synthetic banking customer profile."""

    __tablename__ = "banking_customers"

    customer_id = Column(String(64), primary_key=True, index=True)
    full_name = Column(String(128), nullable=True)
    age = Column(Integer, nullable=True)
    country = Column(String(64), nullable=True, index=True)
    city = Column(String(64), nullable=True)
    latitude: Column[float] = Column(Float, nullable=True)
    longitude: Column[float] = Column(Float, nullable=True)
    account_age_days = Column(Integer, nullable=True)
    average_spending: Column[float] = Column(Float, nullable=True)
    risk_profile = Column(String(32), nullable=True, index=True)
    behavior_pattern = Column(String(64), nullable=True)
    known_devices = Column(JSON, nullable=True)
    usual_countries = Column(JSON, nullable=True)
    fraud_history_count = Column(Integer, nullable=True, default=0)
    created_at = Column(
        DateTime, default=utc_now, server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime, default=utc_now, nullable=False)


class BankingTransaction(Base):
    """Live banking transaction + its fraud-engine score."""

    __tablename__ = "banking_transactions"

    transaction_id = Column(String(80), primary_key=True, index=True)
    customer_id = Column(String(64), index=True, nullable=False)
    customer_name = Column(String(128), nullable=True)
    customer_age = Column(Integer, nullable=True)
    customer_risk_category = Column(String(32), nullable=True)
    timestamp = Column(DateTime, nullable=True, index=True)
    country = Column(String(64), nullable=True, index=True)
    city = Column(String(64), nullable=True)
    latitude: Column[float] = Column(Float, nullable=True)
    longitude: Column[float] = Column(Float, nullable=True)
    ip_address = Column(String(64), nullable=True)
    device_id = Column(String(96), nullable=True)
    browser = Column(String(64), nullable=True)
    operating_system = Column(String(64), nullable=True)
    amount: Column[float] = Column(Float, nullable=False)
    currency = Column(String(8), nullable=True, default="USD")
    transaction_amount: Column[float] = Column(Float, nullable=True)
    transaction_currency = Column(String(8), nullable=True)
    transaction_date = Column(String(16), nullable=True)
    transaction_time = Column(String(16), nullable=True)
    merchant_name = Column(String(128), nullable=True)
    merchant_category = Column(String(64), nullable=True, index=True)
    payment_method = Column(String(48), nullable=True)
    card_type = Column(String(48), nullable=True)
    scenario = Column(String(64), nullable=True, index=True)
    # Additive (Power BI integration): links a transaction to the simulation
    # run that produced it. Nullable so manual /predict calls and pre-existing
    # rows remain valid. Indexed for "filter by run" slicers in Power BI.
    simulation_run_id = Column(String(48), nullable=True, index=True)
    fraud_probability: Column[float] = Column(Float, nullable=True)
    risk_score = Column(Integer, nullable=True, index=True)
    fraud_level = Column(String(32), nullable=True)
    decision = Column(String(32), nullable=True, index=True)
    transaction_status = Column(String(32), nullable=True)
    model_version = Column(String(64), nullable=True)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)


class BankingAlert(Base):
    """Real-time fraud alert produced by the banking scoring engine."""

    __tablename__ = "banking_alerts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(80), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=True)
    customer_name = Column(String(128), nullable=True)
    severity = Column(String(16), nullable=False, default="MEDIUM", index=True)
    fraud_level = Column(String(32), nullable=True)
    risk_score = Column(Integer, nullable=True)
    fraud_probability: Column[float] = Column(Float, nullable=True)
    decision = Column(String(32), nullable=True)
    amount: Column[float] = Column(Float, nullable=True)
    currency = Column(String(8), nullable=True)
    country = Column(String(64), nullable=True)
    city = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    top_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)


class ShapExplanationRecord(Base):
    """Persisted SHAP-style explanation for one banking transaction."""

    __tablename__ = "banking_shap_explanations"

    transaction_id = Column(String(80), primary_key=True, index=True)
    base_value: Column[float] = Column(Float, nullable=False, default=0.0)
    feature_names = Column(JSON, nullable=False)
    shap_values = Column(JSON, nullable=False)
    top_reasons = Column(JSON, nullable=False)
    risk_contribution_score = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


# ======================================================================
# Power BI analytical layer
#
# Additive tables consumed by the vw_powerbi_* DirectQuery views and the
# /api/powerbi/* endpoints. None of these touch the live scoring path:
#
#   * SimulationRun           — one row per simulator start/stop (dim_simulation_run)
#   * ModelBenchmarkResult    — loaded from reports/tables/model_comparison.csv
#   * CostComparisonSummary   — loaded from cost_comparison_summary.csv
#   * CostAnalysisSweep       — loaded from cost_analysis_{model}.csv (per-threshold)
#   * PowerBIExportLog        — audit log of generated export bundles
#
# The benchmark/cost tables are populated by scripts/load_powerbi_warehouse.py
# from the precomputed thesis CSV artefacts. They are NEVER written by the
# training or simulation pipelines, so loading is fully idempotent and the
# original CSVs remain the source of truth.
# ======================================================================


class SimulationRun(Base):
    """Lifecycle + aggregate metrics for one simulator run (dim_simulation_run)."""

    __tablename__ = "simulation_runs"

    run_id = Column(String(48), primary_key=True, index=True)
    started_at = Column(DateTime, nullable=True, index=True)
    stopped_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="ACTIVE", index=True)
    rate_tps = Column(Integer, nullable=True)
    fraud_ratio: Column[float] = Column(Float, nullable=True)
    model_version = Column(String(64), nullable=True)
    generated_transactions = Column(Integer, default=0)
    approved = Column(Integer, default=0)
    suspicious = Column(Integer, default=0)
    blocked = Column(Integer, default=0)
    simulated_frauds = Column(Integer, default=0)
    detected_frauds = Column(Integer, default=0)
    missed_frauds = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    estimated_avoided_loss: Column[float] = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)


class ModelBenchmarkResult(Base):
    """Per-model benchmark metrics for Power BI (fact_model_benchmark)."""

    __tablename__ = "model_benchmark_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(96), nullable=False, index=True)
    precision: Column[float] = Column(Float, nullable=True)
    recall: Column[float] = Column(Float, nullable=True)
    f1: Column[float] = Column(Float, nullable=True)
    mcc: Column[float] = Column(Float, nullable=True)
    roc_auc: Column[float] = Column(Float, nullable=True)
    pr_auc: Column[float] = Column(Float, nullable=True)
    specificity: Column[float] = Column(Float, nullable=True)
    balanced_accuracy: Column[float] = Column(Float, nullable=True)
    # Performance-vs-latency (powers the fact_model_benchmark scatter):
    # training wall-clock seconds + mean per-transaction inference latency (ms).
    training_time: Column[float] = Column(Float, nullable=True)
    inference_time: Column[float] = Column(Float, nullable=True)
    tp = Column(Integer, nullable=True)
    fp = Column(Integer, nullable=True)
    tn = Column(Integer, nullable=True)
    fn = Column(Integer, nullable=True)
    # Enriched during load from the cost-optimal strategy when available.
    threshold_value: Column[float] = Column(Float, nullable=True)
    threshold_type = Column(String(48), nullable=True)
    total_estimated_cost: Column[float] = Column(Float, nullable=True)
    estimated_avoided_loss: Column[float] = Column(Float, nullable=True)
    model_rank = Column(Integer, nullable=True, index=True)
    selected_best_model = Column(Integer, default=0)
    loaded_at = Column(DateTime, default=utc_now, nullable=False)


class CostComparisonSummary(Base):
    """One row per (model, strategy) optimum (fact_cost_analysis summary)."""

    __tablename__ = "cost_comparison_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(96), nullable=False, index=True)
    strategy = Column(String(48), nullable=True, index=True)
    threshold: Column[float] = Column(Float, nullable=True)
    tp = Column(Integer, nullable=True)
    fp = Column(Integer, nullable=True)
    tn = Column(Integer, nullable=True)
    fn = Column(Integer, nullable=True)
    precision: Column[float] = Column(Float, nullable=True)
    recall: Column[float] = Column(Float, nullable=True)
    f1: Column[float] = Column(Float, nullable=True)
    mcc: Column[float] = Column(Float, nullable=True)
    pr_auc: Column[float] = Column(Float, nullable=True)
    roc_auc: Column[float] = Column(Float, nullable=True)
    fraud_loss: Column[float] = Column(Float, nullable=True)
    fp_cost: Column[float] = Column(Float, nullable=True)
    total_cost: Column[float] = Column(Float, nullable=True)
    savings_vs_default: Column[float] = Column(Float, nullable=True)
    savings_pct_vs_default: Column[float] = Column(Float, nullable=True)
    is_optimal_threshold = Column(Integer, default=0)
    loaded_at = Column(DateTime, default=utc_now, nullable=False)


class CostAnalysisSweep(Base):
    """Full per-threshold sweep for one model (fact_threshold_optimization)."""

    __tablename__ = "cost_analysis_sweep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(96), nullable=False, index=True)
    threshold: Column[float] = Column(Float, nullable=False, index=True)
    tp = Column(Integer, nullable=True)
    fp = Column(Integer, nullable=True)
    tn = Column(Integer, nullable=True)
    fn = Column(Integer, nullable=True)
    precision: Column[float] = Column(Float, nullable=True)
    recall: Column[float] = Column(Float, nullable=True)
    f1: Column[float] = Column(Float, nullable=True)
    mcc: Column[float] = Column(Float, nullable=True)
    specificity: Column[float] = Column(Float, nullable=True)
    fraud_loss: Column[float] = Column(Float, nullable=True)
    fp_cost: Column[float] = Column(Float, nullable=True)
    total_cost: Column[float] = Column(Float, nullable=True)
    is_f1_optimal = Column(Integer, default=0)
    is_mcc_optimal = Column(Integer, default=0)
    is_cost_optimal = Column(Integer, default=0)
    loaded_at = Column(DateTime, default=utc_now, nullable=False)


class PowerBIExportLog(Base):
    """Audit log of generated Power BI export bundles."""

    __tablename__ = "powerbi_exports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    export_name = Column(String(128), nullable=False)
    bundle_dir = Column(String(256), nullable=True)
    simulation_run_id = Column(String(48), nullable=True)
    file_count = Column(Integer, nullable=True)
    total_rows = Column(Integer, nullable=True)
    warnings = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=utc_now, nullable=False)
