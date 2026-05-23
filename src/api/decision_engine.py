"""
Real-time fraud decision engine.

Wraps the trained model + preprocessor + feature engineer behind a
single, thread-safe object. The engine:

1. Receives a raw transaction dict
2. Applies the same feature engineering used at training time
3. Scales features with the persisted RobustScaler
4. Predicts fraud probability with the configured model
5. Maps probability to a risk score (0-100)
6. Decides APPROVE / REVIEW / BLOCK using configurable thresholds
7. Builds a human-readable SHAP explanation
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from src.database.models import Decision
from src.explainability.shap_explainer import ShapExplainer
from src.utils.config import PROJECT_ROOT, get_config
from src.utils.io import load_model
from src.utils.logger import get_logger

log = get_logger("api.engine")


@dataclass
class EngineDecision:
    fraud_probability: float
    risk_score: int
    decision: Decision
    threshold: float
    explanation: List[str]
    model_name: str


class FraudDecisionEngine:
    """Singleton-style engine used by the FastAPI service."""

    # Models that work natively with shap.TreeExplainer.
    _TREE_MODELS = ("xgboost", "lightgbm", "catboost", "random_forest")

    def __init__(self, model_name: Optional[str] = None):
        cfg = get_config()
        self.model_name = model_name or cfg.api.default_model
        self.block_threshold = float(cfg.api.block_threshold)
        # REVIEW band is between F1-optimal threshold and block_threshold.
        self.review_threshold = 0.5
        self.enable_shap = bool(cfg.api.enable_shap)
        self._lock = threading.Lock()

        log.info(f"Loading model '{self.model_name}' and feature pipeline...")
        self.model = load_model(self.model_name)
        self.feature_engineer = load_model("feature_engineer")
        self.preprocessor = load_model("preprocessor")
        self.feature_order = self.preprocessor.feature_order

        # ------------------------------------------------------------------
        # SHAP explainer initialisation - robust fallback strategy
        # ------------------------------------------------------------------
        self.explainer: ShapExplainer | None = None
        if self.enable_shap:
            self._setup_shap_explainer()

        log.info("Fraud decision engine ready.")

    # ------------------------------------------------------------------
    def _setup_shap_explainer(self) -> None:
        """Try several strategies so SHAP works for *any* trained model."""
        background = self._load_background_sample()

        # 1) Try the configured model directly (works for XGB/LGBM/RF/CatBoost).
        tried: set[str] = set()
        for candidate_name in (self.model_name, *self._TREE_MODELS):
            if candidate_name in tried:
                continue
            tried.add(candidate_name)
            try:
                raw = (
                    self.model
                    if candidate_name == self.model_name
                    else load_model(candidate_name)
                )
            except FileNotFoundError:
                continue
            candidate = self._unwrap_estimator(raw)
            try:
                self.explainer = ShapExplainer(candidate, background=background)
                if candidate_name != self.model_name:
                    log.warning(
                        f"SHAP fell back to '{candidate_name}' because "
                        f"'{self.model_name}' is not directly explainable."
                    )
                return
            except Exception as exc:
                log.debug(f"SHAP try with '{candidate_name}' failed: {exc}")

        log.warning(
            "SHAP disabled - no explainable model available. "
            "Retrain at least one of: xgboost, lightgbm, random_forest, catboost."
        )

    # ------------------------------------------------------------------
    def _load_background_sample(self, n: int = 100) -> pd.DataFrame | None:
        """Load a small background sample to enable KernelExplainer."""
        parquet = PROJECT_ROOT / "data" / "processed" / "test_features.parquet"
        if not parquet.exists():
            return None
        try:
            df = pd.read_parquet(parquet)
            if "Class" in df.columns:
                df = df.drop(columns=["Class"])
            return df.sample(min(n, len(df)), random_state=42)
        except Exception as exc:
            log.debug(f"Could not load background sample: {exc}")
            return None

    # ------------------------------------------------------------------
    def _align_schema(self, features: pd.DataFrame) -> pd.DataFrame:
        """Guarantee the inference row matches the training schema exactly.

        - Missing columns are added with value 0.0 (typical for rolling
          features computed on an empty streaming buffer).
        - Extra columns are dropped.
        - Column order is forced to match `self.feature_order`.

        This is the canonical "schema contract" pattern: the model
        is never exposed to a frame that differs from what it saw at
        fit time.
        """
        for col in self.feature_order:
            if col not in features.columns:
                features[col] = 0.0
        return features[self.feature_order]

    # ------------------------------------------------------------------
    @staticmethod
    def _unwrap_estimator(m):
        """Drill through CalibratedClassifierCV / FrozenEstimator wrappers."""
        if hasattr(m, "calibrated_classifiers_") and m.calibrated_classifiers_:
            inner = m.calibrated_classifiers_[0].estimator
            # FrozenEstimator wraps the real estimator under .estimator too.
            if hasattr(inner, "estimator"):
                inner = inner.estimator
            return inner
        return m

    def _underlying_estimator(self):
        return self._unwrap_estimator(self.model)

    # ------------------------------------------------------------------
    def score(self, transaction: dict) -> EngineDecision:
        """Score a single transaction."""
        with self._lock:
            features = self.feature_engineer.transform_single(transaction)
            features = self.preprocessor.transform(features)
            features = self._align_schema(features)
            proba = float(self.model.predict_proba(features)[0, 1])

        risk = int(round(proba * 100))
        if proba >= self.block_threshold:
            decision = Decision.BLOCKED
        elif proba >= self.review_threshold:
            decision = Decision.REVIEW
        else:
            decision = Decision.APPROVED

        explanation = self._build_explanation(features, proba, decision)
        return EngineDecision(
            fraud_probability=proba,
            risk_score=risk,
            decision=decision,
            threshold=self.block_threshold,
            explanation=explanation,
            model_name=self.model_name,
        )

    # ------------------------------------------------------------------
    def _build_explanation(self, features: pd.DataFrame, proba: float,
                           decision: Decision) -> List[str]:
        """Produce a list of human-readable bullet points."""
        if decision == Decision.APPROVED:
            return ["Behaviour consistent with the customer's usual transaction patterns."]
        reasons: List[str] = []
        if self.explainer is not None:
            try:
                exp = self.explainer.explain_one(features, top_k=4)
                reasons.extend(exp.top_reasons)
            except Exception as exc:
                log.warning(f"SHAP explanation failed: {exc}")

        # Always add some heuristic fallbacks so a response is never empty.
        if "Is_Night" in features.columns and float(features["Is_Night"].iloc[0]) == 1:
            reasons.append("Transaction occurred during high-risk hours.")
        if "Amount_ZScore" in features.columns and abs(float(features["Amount_ZScore"].iloc[0])) > 3:
            reasons.append("Transaction amount is a statistical outlier.")
        if "Velocity_60s" in features.columns and float(features["Velocity_60s"].iloc[0]) > 5:
            reasons.append("Unusually high transaction velocity (>5 txns in 60 s).")

        # Dedup while preserving order
        seen = set()
        out: list[str] = []
        for r in reasons:
            if r not in seen:
                seen.add(r); out.append(r)
        if not out:
            out.append(f"Fraud probability {proba:.2%} exceeded decision threshold.")
        return out


# ----------------------------------------------------------------------
# Singleton accessor
# ----------------------------------------------------------------------
_ENGINE: FraudDecisionEngine | None = None


def get_engine() -> FraudDecisionEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = FraudDecisionEngine()
    return _ENGINE
