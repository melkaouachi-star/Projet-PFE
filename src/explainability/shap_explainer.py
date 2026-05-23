"""
SHAP-based explainability layer.

Two responsibilities:
1. Offline - generate publication-grade global & local SHAP plots
2. Online  - produce a human-readable explanation for a single
   transaction so the API can return it alongside the decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from src.utils.config import PROJECT_ROOT, get_config
from src.utils.io import load_model, save_model
from src.utils.logger import get_logger

log = get_logger("xai.shap")


# Human-readable templates for the most common SHAP drivers.
_FEATURE_NARRATIVES = {
    "Amount":        ("Unusually high transaction amount.", "Transaction amount is typical."),
    "Log_Amount":    ("Unusually high transaction amount.", "Transaction amount is typical."),
    "Amount_vs_Median": ("Amount strongly deviates from the customer's median.",
                         "Amount close to the customer's usual median."),
    "Amount_ZScore": ("Amount is an outlier (high z-score).", "Amount well within the historical range."),
    "Is_Night":      ("Transaction occurred during high-risk hours (night).",
                      "Transaction occurred during normal business hours."),
    "Hour":          ("Transaction happened at an unusual hour.", "Hour of transaction is unsuspicious."),
    "Velocity_60s":  ("Unusually high transaction velocity in the last minute.",
                      "Normal transaction velocity."),
    "V14":           ("Latent feature V14 strongly indicates fraudulent behaviour.",
                      "Latent feature V14 looks normal."),
    "V17":           ("Latent feature V17 deviates from legitimate-transaction patterns.",
                      "Latent feature V17 looks normal."),
    "V12":           ("Latent feature V12 deviates from legitimate-transaction patterns.",
                      "Latent feature V12 looks normal."),
}


@dataclass
class ShapExplanation:
    feature_names: List[str]
    shap_values: List[float]
    base_value: float
    prediction: float
    top_reasons: List[str]


class ShapExplainer:
    """Wrap a fitted classifier so it can be explained efficiently."""

    def __init__(self, model: Any, background: pd.DataFrame | None = None):
        self.model = model
        # TreeExplainer is preferred when applicable; fall back to KernelExplainer.
        try:
            self._explainer = shap.TreeExplainer(model)
            self._kind = "tree"
        except Exception as tree_exc:
            if background is None or len(background) == 0:
                raise RuntimeError(
                    f"TreeExplainer failed ({tree_exc}) and no background "
                    "dataset was provided for KernelExplainer fallback."
                )
            self._explainer = shap.KernelExplainer(
                lambda x: model.predict_proba(x)[:, 1],
                shap.sample(background, min(100, len(background)), random_state=42),
            )
            self._kind = "kernel"
        log.info(f"SHAP explainer initialised ({self._kind}).")

    # ------------------------------------------------------------------
    # Local explanation
    # ------------------------------------------------------------------
    def explain_one(self, row: pd.DataFrame, top_k: int = 3) -> ShapExplanation:
        """Compute the SHAP explanation of a single transaction."""
        shap_vals = self._explainer(row)
        # shap returns a 3-D array for multi-class TreeExplainer
        values = np.array(shap_vals.values)
        if values.ndim == 3:
            # last axis = classes; pick the fraud class
            values = values[:, :, 1]
        base = float(np.array(shap_vals.base_values).flatten()[-1])
        prediction = float(base + values.sum())

        feature_names = list(row.columns)
        contribs = sorted(zip(feature_names, values.flatten()),
                          key=lambda kv: abs(kv[1]), reverse=True)
        top = contribs[:top_k]
        reasons = []
        for name, val in top:
            pos, neg = _FEATURE_NARRATIVES.get(name, (f"Feature {name} drove the alert.",
                                                       f"Feature {name} is within normal range."))
            reasons.append(pos if val > 0 else neg)

        return ShapExplanation(
            feature_names=feature_names,
            shap_values=values.flatten().tolist(),
            base_value=base,
            prediction=prediction,
            top_reasons=reasons,
        )

    # ------------------------------------------------------------------
    # Global plots
    # ------------------------------------------------------------------
    def global_plots(self, X: pd.DataFrame, sample: int = 2000) -> Dict[str, Path]:
        sample = min(sample, len(X))
        Xs = X.sample(sample, random_state=42)
        shap_vals = self._explainer(Xs)
        values = np.array(shap_vals.values)
        if values.ndim == 3:
            values = values[:, :, 1]

        out_dir = PROJECT_ROOT / get_config().paths.reports_figures
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = {}

        # 1. Beeswarm
        plt.figure(figsize=(10, 7))
        shap.summary_plot(values, Xs, show=False)
        p = out_dir / "30_shap_beeswarm.png"
        plt.savefig(p, dpi=300, bbox_inches="tight"); plt.close()
        paths["beeswarm"] = p

        # 2. Bar (global importance)
        plt.figure(figsize=(10, 6))
        shap.summary_plot(values, Xs, plot_type="bar", show=False)
        p = out_dir / "31_shap_global_importance.png"
        plt.savefig(p, dpi=300, bbox_inches="tight"); plt.close()
        paths["bar"] = p

        # 3. Dependence on top driver
        top_feature = pd.Series(np.abs(values).mean(0), index=Xs.columns).idxmax()
        plt.figure(figsize=(8, 5))
        shap.dependence_plot(top_feature, values, Xs, show=False)
        p = out_dir / f"32_shap_dependence_{top_feature}.png"
        plt.savefig(p, dpi=300, bbox_inches="tight"); plt.close()
        paths["dependence"] = p

        log.info(f"Saved global SHAP figures: {list(paths.values())}")
        return paths

    def waterfall(self, row: pd.DataFrame, fname: str = "33_shap_waterfall.png") -> Path:
        shap_vals = self._explainer(row)
        # shap.plots.waterfall expects a single Explanation
        try:
            exp = shap_vals[0]
            if exp.values.ndim > 1:
                exp = shap.Explanation(values=exp.values[:, 1],
                                       base_values=exp.base_values[1] if hasattr(exp.base_values, "__len__") else exp.base_values,
                                       data=exp.data, feature_names=list(row.columns))
        except Exception:
            exp = shap_vals
        plt.figure(figsize=(8, 6))
        shap.plots.waterfall(exp, show=False)
        out = PROJECT_ROOT / get_config().paths.reports_figures / fname
        plt.savefig(out, dpi=300, bbox_inches="tight"); plt.close()
        log.info(f"Saved waterfall plot: {out}")
        return out


# ----------------------------------------------------------------------
# Singleton for the API
# ----------------------------------------------------------------------
_DEFAULT_EXPLAINER: ShapExplainer | None = None


def get_default_explainer(model_name: str | None = None,
                          background: pd.DataFrame | None = None) -> ShapExplainer:
    """Lazy-loaded singleton used by the FastAPI service."""
    global _DEFAULT_EXPLAINER
    if _DEFAULT_EXPLAINER is None:
        name = model_name or get_config().api.default_model
        model = load_model(name)
        _DEFAULT_EXPLAINER = ShapExplainer(model, background=background)
    return _DEFAULT_EXPLAINER
