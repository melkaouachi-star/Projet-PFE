# Power BI Report — Page-by-Page Specification

10 pages, FinTech/AI dark theme (`fintech_fraud_theme.json`). Every KPI maps to a
measure in `dax_measures.md`; every field maps to a column in
`data_dictionary.csv`. Colours: APPROVED `#22C55E`, SUSPICIOUS/REVIEW `#F59E0B`,
BLOCKED `#EF4444`, brand `#1565C0`/`#38BDF8` on `#07111F` background.

**Global layout convention**
- Top band (height ~110px): page title + KPI cards.
- Left rail (width ~220px): slicers (simulation run, model, decision, date, country, risk band).
- Body: 2–3 visuals max per row; keep whitespace; one "hero" visual per page.

---

## PAGE 1 — Executive Live Fraud Monitoring

**Purpose:** instant real-time view of the platform.

**KPI cards** (measure):
- Nombre total de transactions → `[Total Transactions]`
- APPROVED → `[Approved Transactions]`
- SUSPICIOUS → `[Suspicious Transactions]`
- BLOCKED → `[Blocked Transactions]`
- Fraudes simulées → `[Actual Simulated Frauds]`
- Fraudes détectées → `[Detected Frauds]`
- Fraudes manquées → `[Missed Frauds]`
- False Positives → `[False Positives]`
- Fraud Rate → `[Fraud Rate]` (%)
- Montant total → `[Total Transaction Amount]`
- Montant fraude → `[Total Fraud Amount]`
- Pertes évitées → `[Avoided Fraud Loss]`
- Coût faux positifs → `[False Positive Cost]`
- Coût total estimé → `[Total Estimated Cost]`
- Seuil utilisé → `[Current Block Threshold]`
- Meilleur modèle → `[Best Model]`

**Visuals:**
- Donut: `fact_transactions[decision_status]` by `[Total Transactions]` (fixed colours).
- Line: `[Total Transactions]` by `dim_date`/hour (volume over time).
- Line: `COUNTROWS(fact_fraud_alerts)` by `fact_fraud_alerts[timestamp]` (alerts over time).
- Histogram/column: `fact_transactions[risk_score]` distribution.
- Table (top 10): latest critical alerts — `fact_fraud_alerts` filtered `severity IN {HIGH,CRITICAL}`, sorted `timestamp` desc.
- Map: `fact_transactions[latitude]`/`[longitude]` or `[city]`, bubble size `[Blocked Transactions]`.

**Filters (left rail):** simulation run, model, decision status, date/time, country, city, risk band.

**Auto-refresh:** Format → Page refresh ON (see `directquery_refresh_guide.md`). Counts rise as live transactions arrive.

---

## PAGE 2 — Live Transactions Analysis

**Purpose:** monitor every generated transaction.

**Main visual — table** with columns: `timestamp`, `transaction_id`, `customer_name`,
`city`, `country`, `ip_address`, `amount`, `currency`, `fraud_probability`,
`risk_score`, `threshold_used`, `decision_status`, `real_fraud_label`, `model_name`.

**Conditional formatting:**
- Background of `decision_status` via `[Decision Colour]`.
- Font/background of `risk_score` via `[Risk Score Colour]` (≥70 red, ≥45 amber, else green).

**Drill-through page "Transaction Detail"** (filter on `transaction_id`):
- Cards: amount, fraud_probability, risk_score, decision_status, estimated_avoided_loss, estimated_false_positive_cost.
- Customer block from `dim_customer`.
- Bar: `fact_shap[shap_value]` by `feature_name` for that transaction, coloured by `contribution_direction`.
- Text of `fact_shap[explanation_text]` (top reasons).

---

## PAGE 3 — Fraud Rate and Operational Alerts

**Purpose:** fraud activity + operational pressure.

**KPIs:** `[Fraud Rate]`, `[Alert Rate]`, `[Block Rate]`, `[False Positive Rate]`,
`[Recall]` (frauds), `[Precision]` (blocked), `[Average Fraud Probability]`, `[Average Risk Score]`.

**Visuals:**
- Line: `[Fraud Rate]` over time.
- Stacked column: alerts by `fact_fraud_alerts[severity]`.
- Bar: frauds by `country` / `city`.
- Column: `[Actual Simulated Frauds]` by hour of day.
- Bar: frauds by `merchant_category`.
- Alert timeline (scatter on timestamp) + critical alert list.

**Note box (required):** "`real_fraud_label` exists for simulation validation; in a
real production banking system this label would not be immediately available at
decision time."

---

## PAGE 4 — Losses Avoided and Cost Analysis

**Purpose:** economic effectiveness. Framework `C(s) = FN(s)·C_FN + FP(s)·C_FP`.

**KPI cards:** `[Total Transaction Amount]`, `[Total Fraud Amount]`,
`[Avoided Fraud Loss]`, `[Remaining Fraud Loss]`, `[False Positive Cost]`,
`[Total Estimated Cost]`, `[Net Estimated Saving]`, `[Savings Rate]`,
`[Optimal Threshold]` (from `fact_cost_analysis`).

**Visuals:**
- Bar: `[Avoided Fraud Loss]` vs `[Total Transaction Amount]`.
- Bar: `[Avoided Fraud Loss]` vs `[Remaining Fraud Loss]`.
- Bar: `[False Positive Cost]` vs `[Remaining Fraud Loss]`.
- Line: `fact_threshold_optimization[total_cost]` by `threshold_value` (selected model).
- Line: `savings_vs_default` by `threshold_value`.
- Column: `total_cost` by `model_name` (from `fact_cost_analysis`, `is_optimal_threshold=1`).
- Marker pair: default 0.50 vs cost-optimal threshold.

**Interpretation text block (thesis):** minimising cost ≠ maximising accuracy;
FN and FP have asymmetric financial consequences; the economic threshold may
differ from the F1-optimal threshold.

---

## PAGE 5 — Model Benchmarking

**Purpose:** compare the trained models in `fact_model_benchmark`. **Do not
invent metrics** — use the loaded values. The current project ships 7 models:
logistic_regression, random_forest, xgboost, lightgbm, catboost, voting_ensemble,
stacking_ensemble.

**Visuals:**
- Ranked table: `model_name`, `precision`, `recall`, `f1`, `mcc`, `roc_auc`,
  `pr_auc`, `false_positives`, `false_negatives`, `total_estimated_cost`,
  `estimated_avoided_loss`, sorted by `model_rank`.
- Grouped bar: `f1` / `mcc` / `pr_auc` by model.
- Bar: `false_positives` & `false_negatives` by model.
- Column: `total_estimated_cost` by model.
- Column: `estimated_avoided_loss` by model.
- Radar (top 3 by `model_rank`): precision, recall, f1, mcc, pr_auc.
- Highlight card: `[Best Model]` + `[Best Model F1]` + `[Best Model MCC]`.

**Ranking note:** rank combines technical performance and (when the cost CSVs are
loaded) economic cost; `selected_best_model=1` flags the chosen model. Ranking is
data-driven, not hard-coded.

---

## PAGE 6 — Best Model Deep Dive

**Purpose:** present the selected model.

**Scorecards:** `[Best Model]`, `[Best Model F1]`, `[Best Model MCC]`,
`[Best Model PR AUC]`, `[Best Model Total Cost]`, `[Optimal Threshold]`,
plus precision/recall/FP/FN filtered to `selected_best_model = 1`.

**Visuals:**
- Confusion matrix (matrix visual: tp/fp/fn/tn for the best model).
- PR curve & ROC curve (from `fact_threshold_optimization`: recall vs precision; build TPR/FPR if needed).
- `fact_transactions[fraud_probability]` distribution.
- Decision split donut for the best model's transactions.
- Threshold comparison (0.50 vs F1 vs MCC vs cost) from `fact_cost_analysis`.
- SHAP top features (Page 8 visual, filtered to best model).

**Text blocks:** technical, economic, operational, deployment-suitability,
and limits/precautions justifications.

---

## PAGE 7 — Threshold Optimization

**Purpose:** show how the threshold drives technical & economic performance.
Source: `fact_threshold_optimization` (one model at a time via slicer).

**KPIs:** Default = 0.50; `is_f1_optimal`, `is_mcc_optimal`, `is_cost_optimal`
thresholds; minimum `total_cost`; `[Default vs Optimal Saving]`.

**Visuals (X = `threshold_value`):**
- `total_cost` vs threshold (hero).
- `f1` vs threshold; `mcc` vs threshold.
- `precision` & `recall` vs threshold.
- `false_positives` & `false_negatives` vs threshold.
- avoided-loss proxy vs threshold.

**Reference lines (constant lines):** 0.50, F1-optimal, MCC-optimal, cost-optimal
thresholds (read from the `is_*_optimal` flags).

**Interpretation text:** ready for thesis Chapter 6.

---

## PAGE 8 — SHAP Explainability

**Purpose:** explain why transactions are blocked. Source: `fact_shap`.

**Visuals:**
- Bar: top-10 global features by `AVERAGE(ABS(shap_value))`.
- Ranked SHAP contribution list.
- For a selected blocked transaction: `shap_value` by `feature_name`, coloured by `contribution_direction`.
- Count of transactions blocked per main `explanation_text`.

**User-facing reason wording examples:** montant inhabituellement élevé;
comportement différent du profil habituel; transaction dans une zone à risque;
adresse IP inhabituelle; horaire de transaction atypique; répétition rapide de
transactions.

**Mandatory separation (use distinct visual groups / labels):**
1. Features actually used by the trained model.
2. Contextual fields synthesised for the interface (`classification = synthetic_context`).
3. Raw SHAP contributions (`shap_output`).
4. Business wording derived from SHAP (`business_wording`).

Do **not** claim synthetic geographic/identity variables were present in the
original European dataset unless they were genuinely integrated into training.

---

## PAGE 9 — Contexte Marocain et Applicabilité du Modèle

**Purpose:** discuss adaptation to Morocco. Clearly separate academic contextual
data from simulated platform data.

**Sections (text):** développement des paiements électroniques; évolution des
transactions par carte; adoption du paiement numérique; prédominance du cash;
rôle de la confiance; limites d'un dataset européen pour la fraude marocaine;
nécessité d'un dataset marocain anonymisé; intérêt de l'IA explicable;
modèle recommandé; limites de généralisation.

**Visuals (only when backed by available data):**
- Moroccan card-transaction / amount trends (load your contextual CSV separately).
- `dim_moroccan_context` table — carry the `data_label` disclaimer.
- European training scope vs Moroccan deployment comparison matrix.
- Deployment recommendation matrix.

**Mandatory label** on any Moroccan operational fraud map:
"Données synthétiques de démonstration — non représentatives de la fraude
bancaire réelle au Maroc." (already embedded in the view's `data_label`).

**Do not fabricate Moroccan fraud transaction data.**

---

## PAGE 10 — Simulation Effectiveness and Validation

**Purpose:** use generated data to prove effectiveness. Source: `fact_simulation`
(+ `fact_transactions`).

**KPIs:** generated_transactions, simulated_frauds, detected_frauds, missed_frauds,
false_positives, blocked, approved, `detection_rate`, `[Precision]`, `[Recall]`,
`[F1 Score]`, `[Avoided Fraud Loss]`, `[Remaining Fraud Loss]`,
`[False Positive Cost]`, `[Net Estimated Saving]`.

**Visuals:**
- Clustered column: simulated labels vs model predictions.
- Confusion matrix per run.
- Line: detection_rate / precision_on_blocked over runs (`started_at`).
- Line: cost evolution during the simulation.
- `fraud_probability` distribution split by `real_fraud_label`.
- Column: transactions by `scenario`; effectiveness by `scenario`.

**Filters:** simulation run, scenario, fraud_ratio, rate_tps, model, threshold.
