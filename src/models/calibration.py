"""
Probability calibration utilities.

Calibration is critical in fraud detection because the *decision*
threshold is set on the raw probability and downstream systems (risk
score, customer notifications) treat the probability as a confidence
score.  Boosted trees notoriously produce uncalibrated probabilities.

Implementation note
-------------------
`CalibratedClassifierCV(cv="prefit")` was removed in scikit-learn 1.8.
The recommended replacement is to wrap the already-fitted estimator
with `sklearn.frozen.FrozenEstimator` and pass it in with default cv.
We fall back gracefully on older sklearn versions where
`FrozenEstimator` does not exist (in that case we re-use the legacy
`cv="prefit"` API).
"""
from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV

from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger("models.calibration")

try:
    from sklearn.frozen import FrozenEstimator   # sklearn >= 1.6
    _HAS_FROZEN = True
except ImportError:                              # pragma: no cover
    FrozenEstimator = None                       # type: ignore[assignment]
    _HAS_FROZEN = False


def calibrate(estimator, X_cal, y_cal, method: str | None = None):
    """Wrap an already-fitted estimator into a calibrated classifier.

    Works on both old (<1.8) and new (>=1.6) scikit-learn releases.
    """
    cfg = get_config().calibration
    method = method or cfg.method
    log.info(f"Calibrating model using method='{method}' on {len(X_cal)} rows.")

    if _HAS_FROZEN:
        # Modern API: freeze the estimator so the calibrator does not refit it.
        cal = CalibratedClassifierCV(FrozenEstimator(estimator), method=method)
    else:
        # Legacy API kept for older sklearn installations.
        cal = CalibratedClassifierCV(estimator, method=method, cv="prefit")

    cal.fit(X_cal, y_cal)
    return cal
