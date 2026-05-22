"""Read-only endpoints used by the dashboard."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_session
from src.api.schemas import AlertRecord, PredictionRecord, StatsOut
from src.database import crud

router = APIRouter(prefix="/api/v1", tags=["monitoring"])


@router.get("/predictions", response_model=List[PredictionRecord])
def recent_predictions(limit: int = Query(100, ge=1, le=1000),
                       db: Session = Depends(get_session)):
    return crud.list_recent_predictions(db, limit=limit)


@router.get("/alerts", response_model=List[AlertRecord])
def recent_alerts(limit: int = Query(100, ge=1, le=1000),
                  db: Session = Depends(get_session)):
    return crud.list_recent_alerts(db, limit=limit)


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_session)):
    return crud.stats_summary(db)
