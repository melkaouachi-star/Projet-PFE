"""FastAPI shared dependencies."""
from __future__ import annotations

from fastapi import Depends

from src.api.decision_engine import FraudDecisionEngine, get_engine
from src.database.session import get_session


def engine_dep() -> FraudDecisionEngine:
    return get_engine()


__all__ = ["engine_dep", "get_session", "Depends"]
