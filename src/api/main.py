"""
FastAPI entry point.

Run with:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import explain, monitoring, predictions
from src.api.schemas import HealthOut
from src.utils.logger import get_logger

log = get_logger("api.main")

# Track whether the database was initialised successfully so the health
# endpoint can surface the real state without depending on a live DB call.
_DB_OK: bool = False
_DB_ERROR: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _DB_OK, _DB_ERROR

    cfg = get_config()
    log.info("Starting fraud detection API ...")
    log.info(f"Python {sys.version}")

    # ------------------------------------------------------------------ #
    # Database initialisation — failure is logged but never fatal so that #
    # the /health and / endpoints remain reachable for diagnostics.        #
    # ------------------------------------------------------------------ #
    try:
        from src.database.session import init_db  # deferred to catch import errors
        init_db()
        _DB_OK = True
        log.info("Database initialised successfully.")
    except Exception as exc:
        _DB_ERROR = f"{type(exc).__name__}: {exc}"
        log.error(
            f"Database initialisation FAILED — the API will start without "
            f"database support. Prediction endpoints will return 503 until "
            f"the database is reachable. Error: {_DB_ERROR}"
        )
        log.debug(traceback.format_exc())

    log.info(
        f"API ready -> http://{cfg.api.host}:{cfg.api.port}/docs "
        f"(root: /  health: /health  db_ok: {_DB_OK})"
    )
    yield
    log.info("Shutting down fraud detection API.")


def get_config():
    """Wrapper that surfaces config errors clearly instead of crashing silently."""
    try:
        from src.utils.config import get_config as _get_config
        return _get_config()
    except Exception as exc:
        # Log to stderr directly — the logger itself may not be available yet.
        print(
            f"FATAL: Could not load configuration: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        raise


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

    # ------------------------------------------------------------------ #
    # Root — no dependencies, always responds                             #
    # ------------------------------------------------------------------ #
    @app.get("/", tags=["root"])
    def root():
        """Minimal liveness probe that never depends on DB or model state."""
        return JSONResponse(
            content={
                "service": "fraud-detection-api",
                "version": cfg.project.version,
                "docs": "/docs",
                "db_ok": _DB_OK,
            }
        )

    # ------------------------------------------------------------------ #
    # Health — reports real DB state, never raises                        #
    # ------------------------------------------------------------------ #
    @app.get("/health", response_model=HealthOut, tags=["health"])
    def health():
        """
        Health check that is always reachable.

        Returns ``status: "degraded"`` (HTTP 200) when the database is
        unavailable so that upstream load-balancers keep the instance in
        rotation while the problem is being diagnosed, rather than cycling
        restarts that hide the real error.
        """
        from src.api.decision_engine import _ENGINE  # noqa: PLC0415

        model_loaded = _ENGINE is not None

        if _DB_OK:
            status = "ok"
        else:
            status = "degraded"

        return HealthOut(
            status=status,
            model_loaded=model_loaded,
            model_name=cfg.api.default_model,
            version=cfg.project.version,
        )

    return app


app = create_app()
