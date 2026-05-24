"""CLI: start the FastAPI service with uvicorn."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn

from src.utils.config import get_config


def main() -> None:
    cfg = get_config()
    host = os.getenv("API_HOST", cfg.api.host)
    port = int(os.getenv("PORT", os.getenv("API_PORT", cfg.api.port)))
    reload = bool(cfg.api.reload) and os.getenv("PORT") is None
    print(f"Starting API on {host}:{port}", flush=True)
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
