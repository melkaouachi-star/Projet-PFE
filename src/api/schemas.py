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
