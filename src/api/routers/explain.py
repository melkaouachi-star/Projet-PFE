"""SHAP explanation endpoint."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from src.api.decision_engine import FraudDecisionEngine
from src.api.dependencies import engine_dep
from src.api.schemas import ShapExplanationOut, TransactionIn
from src.utils.logger import get_logger

router = APIRouter(prefix="/api/v1", tags=["explainability"])
log = get_logger("api.explain")


@router.post("/explain", response_model=ShapExplanationOut)
def explain_transaction(
    payload: TransactionIn,
    engine: FraudDecisionEngine = Depends(engine_dep),
):
    """Return a full SHAP breakdown of a transaction without persisting anything."""
    if engine.explainer is None:
        raise HTTPException(status_code=503, detail="SHAP explainer is disabled.")
    raw = payload.to_dict_no_meta()
    features = engine.feature_engineer.transform_single(raw)
    features = engine.preprocessor.transform(features)
    features = engine._align_schema(features)
    exp = engine.explainer.explain_one(features, top_k=5)
    return ShapExplanationOut(
        feature_names=exp.feature_names,
        shap_values=exp.shap_values,
        base_value=exp.base_value,
        prediction=exp.prediction,
        top_reasons=exp.top_reasons,
    )
