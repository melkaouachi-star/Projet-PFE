"""
Central configuration loader.

Loads the YAML config file once and exposes a typed accessor.
All modules MUST go through `get_config()` so that overriding the
config path (e.g. for tests or deployment) is trivial.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"


class Config(dict):
    """Dot-accessible config dictionary."""

    def __getattr__(self, item: str) -> Any:
        try:
            value = self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc
        if isinstance(value, dict):
            return Config(value)
        return value


@lru_cache(maxsize=1)
def get_config(path: str | os.PathLike | None = None) -> Config:
    """Load (and cache) the project configuration."""
    cfg_path = Path(path) if path else Path(os.getenv("FRAUD_CONFIG", DEFAULT_CONFIG_PATH))
    if not cfg_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as fh:
        raw: Dict[str, Any] = yaml.safe_load(fh)
    return Config(raw)


def resolve_path(rel: str) -> Path:
    """Resolve a path declared in config relative to the project root."""
    p = Path(rel)
    return p if p.is_absolute() else PROJECT_ROOT / p
