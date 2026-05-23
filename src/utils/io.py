"""I/O helpers shared across the project (model persistence, JSON dumps)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from .config import PROJECT_ROOT


def save_model(model: Any, name: str, subdir: str = "models_store") -> Path:
    """Persist any picklable object to `models_store/<name>.pkl`."""
    out_dir = PROJECT_ROOT / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.pkl"
    joblib.dump(model, path)
    return path


def load_model(name: str, subdir: str = "models_store") -> Any:
    """Load a previously persisted object."""
    path = PROJECT_ROOT / subdir / f"{name}.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)


def dump_json(payload: dict, path: str | Path) -> Path:
    """Write JSON to disk creating parent directories if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return path
