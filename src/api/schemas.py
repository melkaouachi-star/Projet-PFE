"""Pydantic schemas for the REST API."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ----------------------------------------------------------------------
# Inputs
# ----------------------------------------------------------------------
class TransactionIn(BaseModel):
    """Single incoming transaction (mirrors the Kaggle schema)."""

    model_config = ConfigDict(populate_by_name=True)

    external_id: Optional[str] = Field(None, description="Client-side transaction id")
    Time: float = Field(..., description="Seconds elapsed since the dataset start")
    Amount: float = Field(..., ge=0.0)
    V1: float = 0.0; V2: float = 0.0; V3: float = 0.0; V4: float = 0.0; V5: float = 0.0
    V6: float = 0.0; V7: float = 0.0; V8: float = 0.0; V9: float = 0.0; V10: float = 0.0
    V11: float = 0.0; V12: float = 0.0; V13: float = 0.0; V14: float = 0.0; V15: float = 0.0
    V16: float = 0.0; V17: float = 0.0; V18: float = 0.0; V19: float = 0.0; V20: float = 0.0
    V21: float = 0.0; V22: float = 0.0; V23: float = 0.0; V24: float = 0.0; V25: float = 0.0
    V26: float = 0.0; V27: float = 0.0; V28: float = 0.0

    def to_dict_no_meta(self) -> dict:
        d = self.model_dump()
        d.pop("external_id", None)
        return d


class BatchIn(BaseModel):
    transactions: List[TransactionIn]


# ----------------------------------------------------------------------
# Outputs
# ----------------------------------------------------------------------
class DecisionOut(BaseModel):
    transaction_id: int
    fraud_probability: float
    risk_score: int = Field(..., ge=0, le=100)
    decision: str
    threshold: float
    explanation: List[str]
    model_name: str
    created_at: datetime


class PredictionRecord(BaseModel):
    id: int
    transaction_id: int
    model_name: str
    fraud_probability: float
    risk_score: int
    decision: str
    threshold: float
    explanation: Optional[List[str]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertRecord(BaseModel):
    id: int
    transaction_id: int
    prediction_id: int
    severity: str
    message: str
    acknowledged: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthOut(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    version: str


class ShapExplanationOut(BaseModel):
    feature_names: List[str]
    shap_values: List[float]
    base_value: float
    prediction: float
    top_reasons: List[str]


class StatsOut(BaseModel):
    transactions: int
    predictions: int
    blocked: int
    review: int
    alerts: int


# ======================================================================
# Banking-platform schemas (consumed by src/api/routers/banking.py)
#
# Field names mirror the dicts produced by:
#   - src/simulation/customers.py::CustomerGenerator.generate_customer
#   - src/simulation/transactions.py::TransactionGenerator._build_transaction
# and the assessment payload built by:
#   - src/scoring/dynamic_engine.py::DynamicFraudScoringEngine.score
# Do NOT rename these fields without updating those modules too.
# ======================================================================
from typing import Any, Dict


class BankingTransactionIn(BaseModel):
    """Incoming realistic banking transaction (matches TransactionGenerator output)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    transaction_id: str
    customer_id: str
    customer_name: str
    customer_age: Optional[int] = None
    customer_risk_category: str = "LOW"
    customer_home_country: Optional[str] = None
    customer_home_city: Optional[str] = None
    customer_home_latitude: Optional[float] = None
    customer_home_longitude: Optional[float] = None
    account_age_days: int = 365
    customer_average_spending: float = 120.0
    fraud_history_count: int = 0
    transaction_amount: float = Field(..., ge=0.0)
    transaction_currency: str = "USD"
    merchant_name: str
    merchant_category: str = "Retail"
    transaction_date: Optional[str] = None
    transaction_time: Optional[str] = None
    timestamp: str
    country: str
    city: str
    latitude: float = 0.0
    longitude: float = 0.0
    ip_address: str
    ip_reputation: str = "clean"
    ip_risk_score: int = 0
    is_vpn: bool = False
    is_tor: bool = False
    device_id: Optional[str] = None
    known_device: bool = True
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    payment_method: Optional[str] = None
    card_type: Optional[str] = None
    transaction_status: str = "PENDING"
    recent_transactions_60s: int = 0
    scenario: str = "normal"


class BankingContribution(BaseModel):
    feature_name: str
    feature_value: Any = None
    contribution: float
    shap_value: float
    reason: str


class BankingDecisionOut(BaseModel):
    transaction_id: str
    customer_id: str
    customer_name: str
    timestamp: str
    country: str
    city: str
    latitude: float
    longitude: float
    ip_address: str
    amount: float
    currency: str
    merchant_name: str
    merchant_category: str
    fraud_probability: float
    risk_score: int
    fraud_level: str
    decision: str
    transaction_status: str
    threshold: float
    model_version: str
    top_reasons: List[str]
    contributions: List[BankingContribution]


class BankingTransactionRecord(BaseModel):
    transaction_id: str
    customer_id: str
    customer_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ip_address: Optional[str] = None
    amount: float
    currency: str = "USD"
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    scenario: Optional[str] = None
    fraud_probability: Optional[float] = None
    risk_score: Optional[int] = None
    fraud_level: Optional[str] = None
    decision: Optional[str] = None
    transaction_status: Optional[str] = None
    model_version: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BankingCustomerOut(BaseModel):
    customer_id: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    account_age_days: Optional[int] = None
    average_spending: Optional[float] = None
    risk_profile: Optional[str] = None
    behavior_pattern: Optional[str] = None
    known_devices: Optional[List[str]] = None
    usual_countries: Optional[List[str]] = None
    fraud_history_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class BankingAlertRecord(BaseModel):
    transaction_id: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    severity: str
    fraud_level: Optional[str] = None
    risk_score: Optional[int] = None
    fraud_probability: Optional[float] = None
    decision: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    ip_address: Optional[str] = None
    message: str
    top_reasons: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BankingAnalyticsOut(BaseModel):
    total_transactions: int = 0
    total_amount: float = 0.0
    approved: int = 0
    suspicious: int = 0
    blocked: int = 0
    fraud_rate: float = 0.0
    avg_risk_score: float = 0.0
    high_risk_alerts: int = 0
    estimated_avoided_loss: float = 0.0
    top_countries: List[Dict[str, Any]] = Field(default_factory=list)
    top_merchant_categories: List[Dict[str, Any]] = Field(default_factory=list)
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)


class BankingShapExplanationOut(BaseModel):
    transaction_id: str
    base_value: float
    feature_names: List[str]
    shap_values: List[float]
    top_reasons: List[str]
    risk_contribution_score: Dict[str, Any]


class GenerateCustomersIn(BaseModel):
    count: int = Field(100, ge=1, le=20000)
    seed: int = 42
    persist: bool = True


class SimulatorControlIn(BaseModel):
    rate_tps: int = Field(10, ge=1, le=10000)
    fraud_ratio: float = Field(0.08, ge=0.0, le=1.0)


class SimulatorStatusOut(BaseModel):
    running: bool
    rate_tps: int
    fraud_ratio: float
    generated: int
    started_at: Optional[str] = None
    last_error: Optional[str] = None


# ======================================================================
# Cost / threshold endpoint schemas (Phase 3)
# Consumed by src/api/routers/cost.py.  Mirrors the DataFrame produced by
# src.evaluation.cost_analysis.threshold_sweep + find_optimal_thresholds.
# ======================================================================


class CostAnalysisRowOut(BaseModel):
    threshold: float
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float
    mcc: float
    specificity: float
    fraud_loss: float
    fp_cost: float
    total_cost: float


class CostOptimumOut(BaseModel):
    name: str
    threshold: float
    total_cost: float
    fraud_loss: float
    fp_cost: float
    tp: int
    tn: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    mcc: float


class CostAnalysisOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    source: str  # "offline" or "live"
    mode: str    # "fixed" or "amount_aware"
    currency: str
    baseline_threshold: float
    pr_auc: Optional[float] = None
    roc_auc: Optional[float] = None
    optima: Dict[str, CostOptimumOut]
    sweep: List[CostAnalysisRowOut]
    summary: List[Dict[str, Any]]


class OptimalThresholdOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    strategy: str  # "cost" / "f1" / "mcc" / "default"
    source: str    # "offline" or "live"
    threshold: float
    total_cost: float
    fraud_loss: float
    fp_cost: float
    precision: float
    recall: float
    f1: float
    mcc: float
    tp: int
    fp: int
    tn: int
    fn: int


class ComputeCostAnalysisIn(BaseModel):
    """POST body for live recompute against the banking_transactions table."""
    model_config = ConfigDict(protected_namespaces=())

    model_name: str = "live_dynamic_engine"
    limit: int = Field(5000, ge=10, le=100000)
    mode: Optional[str] = None  # overrides cost_analysis.mode
    c_fn: Optional[float] = None
    c_fp: Optional[float] = None
    baseline_threshold: Optional[float] = None


class ExportInventoryItem(BaseModel):
    name: str
    rows: Optional[int] = None
    available: bool
    endpoint: str
    description: str


class ExportInventoryOut(BaseModel):
    items: List[ExportInventoryItem]
