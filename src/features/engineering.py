"""
Advanced fraud-oriented feature engineering.

All features are deterministic and computable from a single transaction
(plus a rolling history), so that the exact same transformer can run
both in batch (training) and on a live stream (FastAPI inference).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

log = get_logger("features.engineering")


@dataclass
class FraudFeatureEngineer:
    """
    Stateful feature engineer.

    Stores statistics needed at inference time:
    - global median / std of Amount (for z-scores & median ratios)
    - rolling history buffer (for velocity / rolling stats on streams)
    """

    rolling_windows: Iterable[int] = (10, 50, 200)
    enable_log_amount: bool = True
    enable_is_night: bool = True
    enable_hour: bool = True
    enable_rolling: bool = True
    enable_zscore: bool = True
    enable_velocity: bool = True
    enable_interaction: bool = True

    _median_amount: float = 0.0
    _std_amount: float = 1.0
    _mean_amount: float = 0.0
    _history: list = field(default_factory=list)   # for streaming use

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "FraudFeatureEngineer":
        amt = df["Amount"].astype(float)
        self._median_amount = float(amt.median())
        self._std_amount = float(amt.std() or 1.0)
        self._mean_amount = float(amt.mean())
        log.info(f"Fitted feature engineer: median={self._median_amount:.2f}, "
                 f"mean={self._mean_amount:.2f}, std={self._std_amount:.2f}")
        return self

    # ------------------------------------------------------------------
    # Transform (batch)
    # ------------------------------------------------------------------
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()

        if self.enable_log_amount:
            out["Log_Amount"] = np.log1p(out["Amount"].clip(lower=0))

        if self.enable_hour:
            out["Hour"] = (out["Time"] // 3600) % 24

        if self.enable_is_night:
            hour = (out["Time"] // 3600) % 24
            # 00:00-06:00 and 22:00-24:00 considered "high-risk hours"
            out["Is_Night"] = ((hour < 6) | (hour >= 22)).astype(int)

        if self.enable_zscore:
            out["Amount_ZScore"] = (out["Amount"] - self._mean_amount) / self._std_amount
            out["Amount_vs_Median"] = out["Amount"] / (self._median_amount + 1e-6)

        if self.enable_rolling:
            # IMPORTANT: always compute rolling features (even for tiny
            # streaming buffers) so the column schema stays identical
            # between training and inference.  `min_periods=1` is what
            # makes this safe on a buffer of length 1.
            sorted_out = out.sort_values("Time") if len(out) > 1 else out
            amt = sorted_out["Amount"]
            for w in self.rolling_windows:
                sorted_out[f"Amount_RollMean_{w}"] = amt.rolling(w, min_periods=1).mean()
                sorted_out[f"Amount_RollStd_{w}"] = amt.rolling(w, min_periods=1).std().fillna(0)
                if len(sorted_out) > 1:
                    sorted_out[f"Velocity_{w}"] = sorted_out["Time"].rolling(w, min_periods=1).apply(
                        lambda x: (x.iloc[-1] - x.iloc[0]) if len(x) > 1 else 0, raw=False
                    )
                else:
                    sorted_out[f"Velocity_{w}"] = 0.0
            out = sorted_out.sort_index() if len(out) > 1 else sorted_out

        if self.enable_velocity:
            # Fraud frequency proxy: transactions per second over the last minute
            out["Velocity_60s"] = self._compute_velocity_60s(out)

        if self.enable_interaction:
            # Cross-features inspired by the FraudGuard / Banksealer literature.
            if "V14" in out and "V17" in out:
                out["V14_x_V17"] = out["V14"] * out["V17"]
            if "V12" in out and "V10" in out:
                out["V12_x_V10"] = out["V12"] * out["V10"]
            if "Amount" in out and "V17" in out:
                out["Amount_x_V17"] = out["Amount"] * out["V17"]

        out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)

    # ------------------------------------------------------------------
    # Single-row transform for online inference
    # ------------------------------------------------------------------
    def transform_single(self, row: dict) -> pd.DataFrame:
        """
        Transform a single incoming transaction.

        Updates the internal history buffer so that rolling features
        reflect the *streaming* context (recent transactions seen by
        the API).  The buffer is capped at the largest rolling window.
        """
        df = pd.DataFrame([row])
        # Update history then compute features on a windowed view.
        max_w = max(self.rolling_windows) if self.rolling_windows else 1
        self._history.append(row)
        if len(self._history) > max_w * 4:
            self._history = self._history[-max_w * 4:]
        context = pd.DataFrame(self._history)
        full = self.transform(context)
        # Only return the last row (the one we want to score).
        return full.iloc[[-1]].reset_index(drop=True)

    @staticmethod
    def _compute_velocity_60s(df: pd.DataFrame) -> pd.Series:
        """Number of transactions occurring within the previous 60 seconds."""
        sorted_df = df.sort_values("Time").reset_index()
        times = sorted_df["Time"].values
        out = np.zeros(len(times), dtype=int)
        j = 0
        for i in range(len(times)):
            while times[i] - times[j] > 60:
                j += 1
            out[i] = i - j
        sorted_df["v"] = out
        return sorted_df.sort_values("index")["v"].reset_index(drop=True)
