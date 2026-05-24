"""FastAPI shared dependencies."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from src.api.decision_engine import FraudDecisionEngine, get_engine
from src.database.session import get_session
from src.utils.logger import get_logger

log = get_logger("api.dependencies")


def engine_dep() -> FraudDecisionEngine:
    try:
        return get_engine()
    except Exception as exc:
        log.exception(f"Could not load fraud decision engine: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Fraud decision engine is not available. Check API deployment logs.",
        ) from exc


__all__ = ["engine_dep", "get_session", "Depends"]
