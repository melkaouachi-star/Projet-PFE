"""ORM models for the fraud-detection platform."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
)

from src.database.session import Base


class Decision(str, enum.Enum):
    APPROVED = "APPROVED"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


class Transaction(Base):
    """A raw incoming transaction."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(64), index=True, nullable=True)
    time_seconds = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Prediction(Base):
    """Output of the fraud-detection engine for one transaction."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, index=True, nullable=False)
    model_name = Column(String(64), nullable=False)
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    threshold = Column(Float, nullable=False)
    decision = Column(Enum(Decision), nullable=False)
    explanation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FraudAlert(Base):
    """Alerts surfaced to the security analysts / customer."""
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, index=True, nullable=False)
    prediction_id = Column(Integer, index=True, nullable=False)
    severity = Column(String(16), nullable=False, default="HIGH")
    message = Column(Text, nullable=False)
    acknowledged = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


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
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    account_age_days = Column(Integer, nullable=True)
    average_spending = Column(Float, nullable=True)
    risk_profile = Column(String(32), nullable=True, index=True)
    behavior_pattern = Column(String(64), nullable=True)
    known_devices = Column(JSON, nullable=True)
    usual_countries = Column(JSON, nullable=True)
    fraud_history_count = Column(Integer, nullable=True, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BankingTransaction(Base):
    """Live banking transaction + its fraud-engine score."""

    __tablename__ = "banking_transactions"

    transaction_id = Column(String(80), primary_key=True, index=True)
    customer_id = Column(String(64), index=True, nullable=False)
    customer_name = Column(String(128), nullable=True)
    timestamp = Column(DateTime, nullable=True, index=True)
    country = Column(String(64), nullable=True, index=True)
    city = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    ip_address = Column(String(64), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=True, default="USD")
    merchant_name = Column(String(128), nullable=True)
    merchant_category = Column(String(64), nullable=True, index=True)
    scenario = Column(String(64), nullable=True, index=True)
    fraud_probability = Column(Float, nullable=True)
    risk_score = Column(Integer, nullable=True, index=True)
    fraud_level = Column(String(32), nullable=True)
    decision = Column(String(32), nullable=True, index=True)
    transaction_status = Column(String(32), nullable=True)
    model_version = Column(String(64), nullable=True)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


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
    fraud_probability = Column(Float, nullable=True)
    decision = Column(String(32), nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(8), nullable=True)
    country = Column(String(64), nullable=True)
    city = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    top_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ShapExplanationRecord(Base):
    """Persisted SHAP-style explanation for one banking transaction."""

    __tablename__ = "banking_shap_explanations"

    transaction_id = Column(String(80), primary_key=True, index=True)
    base_value = Column(Float, nullable=False, default=0.0)
    feature_names = Column(JSON, nullable=False)
    shap_values = Column(JSON, nullable=False)
    top_reasons = Column(JSON, nullable=False)
    risk_contribution_score = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
