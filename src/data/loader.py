"""
Dataset loader for the European Credit Card Fraud Detection dataset.

The raw CSV is expected at `data/raw/creditcard.csv` (download from
Kaggle: mlg-ulb/creditcardfraud).  This loader is intentionally thin -
it only validates schema and returns a DataFrame, so it can be reused
both by the offline training pipeline and the online API.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from src.utils.config import PROJECT_ROOT, get_config
from src.utils.logger import get_logger

log = get_logger("data.loader")


def load_creditcard_dataset(path: Optional[str | Path] = None) -> pd.DataFrame:
    """
    Load the European credit-card fraud dataset.

    Parameters
    ----------
    path : optional override for the raw CSV path.

    Returns
    -------
    DataFrame with columns: Time, V1..V28, Amount, Class
    """
    cfg = get_config()
    csv_path = Path(path) if path else PROJECT_ROOT / cfg.paths.data_raw
    log.info(f"Loading dataset from {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}. Download it from "
            "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud "
            "and place it under data/raw/creditcard.csv"
        )

    df = pd.read_csv(csv_path)
    _validate_schema(df, cfg)
    log.info(f"Loaded {len(df):,} transactions ({df[cfg.data.target_column].sum():,} fraudulent).")
    return df


def _validate_schema(df: pd.DataFrame, cfg) -> None:
    """Ensure the dataset has the expected columns."""
    required = {cfg.data.time_column, cfg.data.amount_column, cfg.data.target_column}
    required.update(cfg.data.pca_features)
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")


def chronological_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    time_col: str = "Time",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split a dataset *chronologically* to avoid temporal leakage.

    Random splits in fraud detection are dangerous because fraud
    patterns drift over time - the model would otherwise be evaluated
    on a distribution that future production traffic will never match.
    """
    df_sorted = df.sort_values(time_col).reset_index(drop=True)
    cutoff = int(len(df_sorted) * (1 - test_size))
    return df_sorted.iloc[:cutoff].copy(), df_sorted.iloc[cutoff:].copy()
