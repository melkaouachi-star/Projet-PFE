"""
CLI: generate global SHAP figures (beeswarm / bar / dependence) and one
example waterfall plot for a real fraudulent transaction.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.explainability.shap_explainer import ShapExplainer
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.io import load_model
from src.utils.logger import get_logger

log = get_logger("scripts.shap")


def main() -> None:
    cfg = get_config()
    model_name = cfg.api.default_model
    test = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "test_features.parquet")
    X = test.drop(columns=["Class"])
    y = test["Class"]

    model = load_model(model_name)
    explainer = ShapExplainer(model._underlying_estimator() if hasattr(model, "_underlying_estimator") else model,
                              background=X.sample(min(500, len(X)), random_state=42))
    explainer.global_plots(X, sample=2000)

    fraud = X.loc[y == 1].iloc[[0]] if (y == 1).any() else X.iloc[[0]]
    explainer.waterfall(fraud, fname="33_shap_waterfall_example.png")
    log.info("SHAP plots regenerated.")


if __name__ == "__main__":
    main()
