"""Unit tests for the feature engineer."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.engineering import FraudFeatureEngineer


def _make_df(n: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "Time": np.linspace(0, 86400, n),
        "Amount": rng.uniform(1, 500, n),
        "Class": rng.integers(0, 2, n),
        **{f"V{i}": rng.normal(0, 1, n) for i in range(1, 29)},
    })


def test_fit_transform_adds_expected_features():
    df = _make_df()
    fe = FraudFeatureEngineer().fit(df)
    out = fe.transform(df)
    assert "Log_Amount" in out.columns
    assert "Is_Night" in out.columns
    assert "Amount_ZScore" in out.columns
    assert "Hour" in out.columns


def test_transform_single_returns_one_row():
    df = _make_df()
    fe = FraudFeatureEngineer().fit(df)
    one = df.iloc[0].drop("Class").to_dict()
    res = fe.transform_single(one)
    assert len(res) == 1
    assert "Log_Amount" in res.columns
