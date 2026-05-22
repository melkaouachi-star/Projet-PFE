"""CLI entry point: generate every EDA figure."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.eda import run_full_eda
from src.data.loader import load_creditcard_dataset
from src.utils.logger import get_logger

log = get_logger("scripts.eda")


def main() -> None:
    df = load_creditcard_dataset()
    paths = run_full_eda(df)
    log.info(f"EDA completed - {len(paths)} figures generated.")


if __name__ == "__main__":
    main()
