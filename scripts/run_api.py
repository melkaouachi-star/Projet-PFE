"""CLI: start the FastAPI service with uvicorn."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn

from src.utils.config import get_config


def main() -> None:
    cfg = get_config()
    uvicorn.run(
        "src.api.main:app",
        host=cfg.api.host,
        port=cfg.api.port,
        reload=bool(cfg.api.reload),
    )


if __name__ == "__main__":
    main()
