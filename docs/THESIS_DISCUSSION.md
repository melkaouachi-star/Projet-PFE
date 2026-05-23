# Critical Discussion - Thesis-Ready Notes

This document collects the analytical material a Master's thesis
needs to discuss alongside the experimental results.

---

## 1. Dataset

The **European Credit Card Fraud Detection** dataset
(Pozzolo et al., 2015; Kaggle: *mlg-ulb/creditcardfraud*) gathers
284,807 transactions issued by European cardholders over two days in
September 2013, of which only 492 (0.17 %) are fraudulent.

### Limitations

1. **PCA-anonymised features.** Twenty-eight of the thirty input
   features (`V1`-`V28`) are the output of an undisclosed PCA. The
   semantics of each component are lost, which weakens feature
   engineering and severely limits the actionable insights derivable
   from the model. Only `Time` and `Amount` remain interpretable.
2. **Very short observation window (48 h).** Concept drift, weekly
   seasonality and long-term behaviour cannot be modelled.
3. **Extreme class imbalance.** The 0.17 % fraud rate forces every
   evaluator to look at PR-AUC, MCC and F1, not ROC-AUC.
4. **No merchant, geolocation, device or user identifiers**, despite
   these being the highest-signal features in real fraud-detection
   stacks.
5. **No Moroccan / North-African data.** Fraud patterns differ
   significantly between European credit-card systems
   (chip-and-PIN dominant, SEPA settlement, EU-PSD2 SCA) and the
   Moroccan market (mixed magnetic-strip + EMV adoption, frequent
   "cardless" mobile money fraud, MAD currency caps).

### Generalisation bias - European vs Moroccan banking

| Dimension | European (this dataset) | Moroccan ecosystem |
|-----------|-------------------------|--------------------|
| Card technology | EMV chip-and-PIN ubiquitous | Mixed chip + magnetic |
| Regulation | PSD2 + SCA + GDPR | Bank Al-Maghrib Circulars (BAM 2/G/19, etc.) |
| Currency volatility | Stable EUR | MAD with controlled peg |
| Average ticket | Higher, lower variance | Lower, higher variance |
| Dominant fraud | CNP cross-border | OTP intercept / SIM-swap |
| Available labels | Rich processor labels | Often partial |

A model trained exclusively on European data can therefore **over-fit
European fraud signatures** (e.g. test-charges with rapid card-not-
present escalation) and *miss* fraud signatures that are typical
elsewhere (e.g. mobile-money cash-out chains). This is one of the
strongest arguments in favour of *transfer learning* and *federated
learning* in a Moroccan deployment - and one of the most important
caveats to surface in the dissertation.

---

## 2. Class-Imbalance Strategies

| Strategy | Effect on Recall | Effect on Precision | Business risk |
|----------|------------------|---------------------|---------------|
| None | Low | High | Many missed frauds (high FN cost). |
| Random undersampling | Medium | Low | Drops signal, increases FP rate. |
| SMOTE | High | Medium | Synthetic noise near borders -> shaky generalisation. |
| BorderlineSMOTE | High | Medium-High | Best classic SMOTE variant. |
| ADASYN | High | Medium | Aggressive on hard examples - can overshoot. |
| **SMOTEENN** | High | High | Recommended default - hybrid clean-up. |
| Tomek Links | Marginal | High | Conservative, mainly removes ambiguous majority. |
| Class-weight (cost-sensitive) | Medium-High | High | No data manipulation - production-safe. |

**Recommendation for the thesis:** report a benchmark table across
all strategies, but ship `SMOTEENN` *or* `class_weight` in
production.  Cost-sensitive learning is preferable when downstream
regulators audit the model: nothing synthetic enters training.

---

## 3. Temporal Validation

A *random* train/test split would let the model peek into the future.
With only 48 hours of data, even small leakage inflates metrics by
several percentage points of PR-AUC.  We enforce three protections:

1. **Chronological holdout** for the final evaluation
   (`chronological_split` in `src/data/loader.py`).
2. **TimeSeriesSplit** for cross-validation
   (`src/training/validation.py`) - each fold predicts the next
   chronological block, never a past one.
3. **All preprocessors fitted on the training fold only**
   (`FraudPreprocessor`, `FraudFeatureEngineer`). The rolling
   statistics and z-score baselines never see the test window.

---

## 4. Explainability in Banking AI

In the EU, Article 22 of the GDPR plus the upcoming AI Act explicitly
require *meaningful explanations* whenever an automated decision has
a significant effect on a natural person - blocking a card payment
qualifies. In Morocco, **Law 09-08** on personal-data protection and
the **CNDP** guidelines on automated decisioning impose comparable
duties.

The thesis-ready argument is:

- ROC-AUC = 0.99 is meaningless without per-decision justification.
- SHAP provides locally faithful, globally consistent attributions
  (Lundberg & Lee, 2017).
- Our system pairs **SHAP values** with a curated narrative
  template (`_FEATURE_NARRATIVES` in `shap_explainer.py`) so the
  end-user sees plain-language reasons, not raw coefficients.

---

## 5. False Positive Reduction

Each blocked legitimate card transaction has a non-trivial cost: lost
revenue, customer call-centre minutes, churn risk. We implement four
stacked techniques to keep FP rates low:

1. **Probability calibration** (isotonic) so the threshold means what
   it says.
2. **Threshold optimisation** by F1 / MCC / business-cost
   (`src/training/threshold.py`).
3. **Two-stage decision**: APPROVE / REVIEW / BLOCK -
   the REVIEW band sends ambiguous transactions to a human analyst
   rather than auto-blocking them.
4. **Ensemble filtering** via stacking - weak signals from any single
   learner are diluted before reaching the decision layer.

---

## 6. Concept Drift & Evolving Fraud Strategies

Fraud schemes evolve (card-testing on online subscriptions, BIN
attacks, OTP intercepts, account-takeover via SIM-swap). The model
must be re-trained on a rolling window, and monitored with:

- **Population Stability Index (PSI)** on input features.
- **Drift dashboards** comparing the historical SHAP top-features to
  the live ones.
- **Champion / challenger** A/B testing of model candidates.

These hooks are exposed via the API monitoring endpoints
(`/api/v1/stats`, `/predictions`) and can be plugged into Grafana or
Evidently in production.

---

## 7. Ethical Concerns

- **Customer blocking risk.** False positives can leave a legitimate
  customer stranded abroad without payment.  Adaptive thresholds
  (REVIEW band) and human-in-the-loop reviews are non-negotiable.
- **Disparate impact.** PCA-anonymised features hide whether the
  model relies on a proxy of a protected attribute - any production
  deployment must perform a fairness audit on raw features once they
  become available.
- **Right to be forgotten.** Transactions stored in the prediction
  log must respect retention limits (GDPR Article 5).

---

## 8. Summary of Contributions

This thesis delivers:

1. A **reproducible end-to-end pipeline** for credit-card fraud
   detection with strict anti-leakage guarantees.
2. A **benchmark of imbalance strategies and model families**
   (LR, RF, XGB, LGBM, CatBoost, Voting, Stacking) under
   chronological cross-validation.
3. A **calibrated, threshold-optimised ensemble** that minimises
   business cost (`fp_cost`, `fn_cost`).
4. A **production-ready FastAPI service** with a real-time
   decision engine and a SHAP-backed explanation layer.
5. A **monitoring dashboard** suitable for live demonstrations
   during the thesis defence.
6. A **critical discussion** of dataset bias, concept drift,
   ethical concerns and Moroccan-specific generalisation
   limitations.
