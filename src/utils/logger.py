"""
Centralised structured logger backed by loguru.

Provides one helper - `get_logger(name)` - used everywhere in the
codebase.  Logs go both to stdout (coloured) and to a rotating file
inside the `logs/` folder.
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from .config import PROJECT_ROOT, get_config

_INITIALISED = False


def _initialise_logger() -> None:
    """Configure handlers exactly once."""
    global _INITIALISED
    if _INITIALISED:
        return

    cfg = get_config()
    log_dir = PROJECT_ROOT / cfg.paths.logs
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        level=cfg.logging.level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level:<8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> | {message}",
    )
    logger.add(
        log_dir / "fraud_detection.log",
        level=cfg.logging.level,
        rotation=cfg.logging.rotation,
        retention=cfg.logging.retention,
        encoding="utf-8",
        enqueue=True,
    )
    _INITIALISED = True


def get_logger(name: str = "fraud"):
    """Return a configured loguru logger bound to a component name."""
    _initialise_logger()
    return logger.bind(component=name)
