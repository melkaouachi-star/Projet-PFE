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
