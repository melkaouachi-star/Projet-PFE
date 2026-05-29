"""
FastAPI entry point.

Run with:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.routers import explain, monitoring, predictions
from src.api.schemas import HealthOut
from src.database.session import init_db
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_config()
    host = os.getenv("API_HOST", cfg.api.host)
    port = os.getenv("PORT", os.getenv("API_PORT", str(cfg.api.port)))
    log.info("Starting fraud detection API ...")
    try:
        init_db()
    except Exception as exc:
        log.exception(f"Database initialisation failed: {exc}")
    log.info(f"API ready -> http://{host}:{port}/docs "
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

    # Banking platform router (live simulator, SSE/WebSocket, fraud alerts,
    # customers, SHAP). Guarded so a partial outage in this layer cannot
    # take down the core /api/v1/predict + /health endpoints.
    try:
        from src.api.routers import banking  # noqa: WPS433 (local import on purpose)

        app.include_router(banking.router)
    except Exception as exc:  # pragma: no cover - defensive boot guard
        log.exception(f"Banking router not registered: {exc}")

    # Cost-analysis + optimal-threshold endpoints (Phase 3).
    try:
        from src.api.routers import cost as cost_router  # noqa: WPS433

        app.include_router(cost_router.router)
    except Exception as exc:  # pragma: no cover - defensive boot guard
        log.exception(f"Cost router not registered: {exc}")

    # Export endpoints (CSV + Power BI ZIP bundle, Phase 3).
    try:
        from src.api.routers import exports as exports_router  # noqa: WPS433

        app.include_router(exports_router.router)
    except Exception as exc:  # pragma: no cover - defensive boot guard
        log.exception(f"Exports router not registered: {exc}")

    # Power BI integration endpoints (/api/powerbi/*, Phase 4).
    # DirectQuery is the canonical path; these JSON endpoints are the
    # Import/Web-connector fallback and a health surface for the views.
    try:
        from src.api.routers import powerbi as powerbi_router  # noqa: WPS433

        app.include_router(powerbi_router.router)
    except Exception as exc:  # pragma: no cover - defensive boot guard
        log.exception(f"Power BI router not registered: {exc}")

    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/dashboard", tags=["dashboard"])
        def dashboard():
            return FileResponse(static_dir / "dashboard.html")

    @app.get("/cost-analysis", tags=["cost-analysis"], include_in_schema=False)
    def cost_analysis_alias(model: str):
        return RedirectResponse(url=f"/api/v1/cost-analysis?model={model}", status_code=307)

    @app.get("/optimal-threshold", tags=["cost-analysis"], include_in_schema=False)
    def optimal_threshold_alias(model: str, strategy: str = "cost"):
        return RedirectResponse(
            url=f"/api/v1/optimal-threshold?model={model}&strategy={strategy}",
            status_code=307,
        )

    @app.get("/export/simulation", tags=["exports"], include_in_schema=False)
    def export_simulation_alias():
        return RedirectResponse(url="/api/v1/export/simulation-summary.csv", status_code=307)

    @app.get("/export/powerbi", tags=["exports"], include_in_schema=False)
    def export_powerbi_alias():
        return RedirectResponse(url="/api/v1/export/powerbi.zip", status_code=307)

    @app.get("/", tags=["root"])
    def root():
        return {
            "service": "fraud-detection-api",
            "version": cfg.project.version,
            "docs": "/docs",
            "dashboard": "/dashboard",
            "banking": {
                "predict": "/predict",
                "transactions": "/transactions",
                "customers": "/customers",
                "fraud_alerts": "/fraud-alerts",
                "live_stream": "/live-stream",
                "websocket": "/ws/live-stream",
                "cost_analysis": "/api/v1/cost-analysis",
                "exports": "/api/v1/export/inventory",
            },
            "powerbi": {
                "views": "/api/powerbi/views",
                "transactions": "/api/powerbi/transactions",
                "kpis": "/api/powerbi/kpis",
                "model_benchmark": "/api/powerbi/model-benchmark",
                "simulation_summary": "/api/powerbi/simulation-summary",
                "export_bundle": "/api/powerbi/export-bundle",
            },
        }

    @app.get("/health", response_model=HealthOut, tags=["health"])
    def health():
        return HealthOut(
            status="ok",
            model_loaded=False,
            model_name=cfg.api.default_model,
            version=cfg.project.version,
        )

    return app


app = create_app()
