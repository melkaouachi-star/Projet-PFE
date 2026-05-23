"""
Anti-leakage validation utilities.

We *only* use chronological validation (TimeSeriesSplit) because in
production the model scores transactions that occur *after* the ones
it was trained on.  A standard K-Fold would shuffle past and future
together and grossly over-estimate live performance.
"""
from __future__ import annotations

from typing import Iterator, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger("training.validation")


def time_series_splits(X: pd.DataFrame, n_splits: int | None = None
                       ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    """
    Yield train/validation index pairs that respect chronological order.

    Assumes the DataFrame is already sorted by time.
    """
    cfg = get_config().training
    n = n_splits or cfg.n_splits
    log.info(f"Generating {n} chronological folds (TimeSeriesSplit).")
    splitter = TimeSeriesSplit(n_splits=n)
    yield from splitter.split(X)
