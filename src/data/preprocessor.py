"""
Preprocessing pipeline: scaling, NaN handling, feature ordering.

The preprocessor is stateful (fit/transform) so that the same object
serialised at training time can be reloaded and applied to a single
incoming transaction at inference time inside the FastAPI service.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

from src.utils.logger import get_logger

log = get_logger("data.preprocessor")


@dataclass
class FraudPreprocessor:
    """Robust-scales `Time` and `Amount`; leaves PCA features untouched."""

    scale_cols: List[str] = field(default_factory=lambda: ["Time", "Amount"])
    _scaler: RobustScaler | None = None
    _feature_order: List[str] | None = None

    def fit(self, df: pd.DataFrame) -> "FraudPreprocessor":
        log.info(f"Fitting preprocessor on {len(df):,} rows.")
        self._scaler = RobustScaler().fit(df[self.scale_cols])
        self._feature_order = [c for c in df.columns if c != "Class"]
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._scaler is None:
            raise RuntimeError("Preprocessor must be fitted before transform().")
        out = df.copy()
        # Inference may pass a row without Class - guard accordingly.
        scale_cols = [c for c in self.scale_cols if c in out.columns]
        out[scale_cols] = self._scaler.transform(out[scale_cols])
        # Fill any residual NaNs (rolling features at the start of the stream).
        out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)

    @property
    def feature_order(self) -> List[str]:
        if self._feature_order is None:
            raise RuntimeError("Preprocessor not fitted yet.")
        return self._feature_order
