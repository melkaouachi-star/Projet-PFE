"""
FastAPI entry point.

Run with:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import engine_dep
from src.api.routers import explain, monitoring, predictions
from src.api.schemas import HealthOut
from src.database.session import init_db
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_config()
    log.info("Starting fraud detection API ...")
    init_db()
    # Eagerly load the engine so the first request isn't slow.
    try:
        _ = engine_dep()
    except FileNotFoundError as exc:
        log.warning(f"Could not preload model (run training first): {exc}")
    log.info(f"API ready -> http://{cfg.api.host}:{cfg.api.port}/docs "
             f"(root: /  health: /health)")
    yield
    log.info("Shutting down fraud detection API.")


def create_app() -> FastAPI:
    cfg = get_config()
    app = FastAPI(
        title="Real-time Credit Card Fraud Detection API",
        description=(
            "Production-grade fraud detection backend. "
            "Provides real-time scoring, explainable decisions and "
            "live monitoring endpoints."
        ),
        version=cfg.project.version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.api.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(predictions.router)
    app.include_router(explain.router)
    app.include_router(monitoring.router)

    @app.get("/", tags=["root"])
    def root():
        return {
            "service": "fraud-detection-api",
            "version": cfg.project.version,
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthOut, tags=["health"])
    def health(engine=Depends(engine_dep)):
        return HealthOut(
            status="ok",
            model_loaded=engine.model is not None,
            model_name=engine.model_name,
            version=cfg.project.version,
        )

    return app


app = create_app()
