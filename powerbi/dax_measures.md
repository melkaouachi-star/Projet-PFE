# DAX Measures — FinTech Fraud Detection Dashboard

All measures below are **ready to copy** into Power BI Desktop (Modeling → New
measure). They reference the **actual** column names exposed by the
`vw_powerbi_*` views (see `sql/powerbi_views_postgres.sql` /
`sql/powerbi_views_sqlite.sql` and `powerbi/data_dictionary.csv`).

## Table-name convention used here

When you connect the views, rename each query to the star-schema table name in
`powerbi/star_schema.md`. The measures assume these names:

| Measure table reference | Source view / table              |
|-------------------------|----------------------------------|
| `fact_transactions`     | `vw_powerbi_live_transactions`   |
| `fact_fraud_alerts`     | `vw_powerbi_fraud_alerts`        |
| `fact_shap`             | `vw_powerbi_shap_explanations`   |
| `fact_model_benchmark`  | `vw_powerbi_model_benchmark`     |
| `fact_cost_analysis`    | `vw_powerbi_cost_comparison`     |
| `fact_threshold_optimization` | `vw_powerbi_threshold_optimization` |
| `fact_simulation`       | `vw_powerbi_simulation_effectiveness` |
| `dim_customer`          | `banking_customers`              |

Create a dedicated empty table named **`_Measures`** (Enter Data → one blank
column) and host every measure there so the field list stays clean.

## Important scale & constant notes (do not guess)

* `fact_transactions[fraud_probability]` is on a **0..100** scale. The view also
  exposes `fraud_probability_pct` (0..1). Use the `_pct` column for "%" format.
* `real_fraud_label` is the **simulation ground truth** (`scenario <> 'normal'`).
  It is used only to *validate* the model; in production it is not available at
  decision time.
* Economic constants below mirror `configs/config.yaml`:
  * **FP unit cost = 12.5** (`powerbi.fp_unit_cost` = 8.0 + 3.0 + 1.5).
  * **Block threshold = 70** on the 0..100 risk scale (`powerbi.block_threshold`).
  * The amount-aware `C_FN` used by the **offline** cost pipeline lives in
    `fact_cost_analysis`/`fact_threshold_optimization`; the live measures below
    use the realised transaction `amount` for avoided/remaining fraud loss.

---

## 1. Basic monitoring

```dax
Total Transactions = COUNTROWS ( fact_transactions )
```
```dax
Approved Transactions =
CALCULATE ( [Total Transactions], fact_transactions[decision_status] = "APPROVED" )
```
```dax
Suspicious Transactions =
CALCULATE (
    [Total Transactions],
    fact_transactions[decision_status] IN { "SUSPICIOUS", "REVIEW" }
)
```
```dax
Blocked Transactions =
CALCULATE ( [Total Transactions], fact_transactions[decision_status] = "BLOCKED" )
```
```dax
Total Transaction Amount = SUM ( fact_transactions[amount] )
```
```dax
Average Transaction Amount = AVERAGE ( fact_transactions[amount] )
```
```dax
Latest Transaction Timestamp = MAX ( fact_transactions[created_at] )
```
```dax
Current Block Threshold = 70        -- config powerbi.block_threshold (0..100 scale)
```

---

## 2. Fraud monitoring (confusion matrix from simulation ground truth)

```dax
Actual Simulated Frauds =
CALCULATE ( [Total Transactions], fact_transactions[real_fraud_label] = 1 )
```
```dax
True Positives =
CALCULATE (
    [Total Transactions],
    fact_transactions[real_fraud_label] = 1,
    fact_transactions[decision_status] = "BLOCKED"
)
```
```dax
False Negatives =
CALCULATE (
    [Total Transactions],
    fact_transactions[real_fraud_label] = 1,
    fact_transactions[decision_status] <> "BLOCKED"
)
```
```dax
False Positives =
CALCULATE (
    [Total Transactions],
    fact_transactions[real_fraud_label] = 0,
    fact_transactions[decision_status] = "BLOCKED"
)
```
```dax
True Negatives =
CALCULATE (
    [Total Transactions],
    fact_transactions[real_fraud_label] = 0,
    fact_transactions[decision_status] <> "BLOCKED"
)
```
```dax
Detected Frauds = [True Positives]
```
```dax
Missed Frauds = [False Negatives]
```
```dax
Fraud Rate =
DIVIDE ( [Actual Simulated Frauds], [Total Transactions] )
```
```dax
Block Rate = DIVIDE ( [Blocked Transactions], [Total Transactions] )
```
```dax
Alert Rate =
DIVIDE ( [Blocked Transactions] + [Suspicious Transactions], [Total Transactions] )
```
```dax
False Positive Rate =
DIVIDE ( [False Positives], [False Positives] + [True Negatives] )
```
```dax
Detection Rate = DIVIDE ( [Detected Frauds], [Actual Simulated Frauds] )
```
```dax
Recall = DIVIDE ( [True Positives], [True Positives] + [False Negatives] )
```
```dax
Precision = DIVIDE ( [True Positives], [True Positives] + [False Positives] )
```
```dax
F1 Score =
VAR p = [Precision]
VAR r = [Recall]
RETURN DIVIDE ( 2 * p * r, p + r )
```
```dax
Average Fraud Probability = AVERAGE ( fact_transactions[fraud_probability] )   -- 0..100
```
```dax
Average Risk Score = AVERAGE ( fact_transactions[risk_score] )
```

---

## 3. Economic evaluation (asymmetric cost framework)

`C(s) = FN(s) × C_FN + FP(s) × C_FP`. The live page uses realised amounts for
avoided/remaining loss and the FP unit cost (12.5) for the FP side.

```dax
Total Fraud Amount =
CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[real_fraud_label] = 1 )
```
```dax
Avoided Fraud Loss = SUM ( fact_transactions[estimated_avoided_loss] )
```
```dax
Remaining Fraud Loss =
CALCULATE (
    SUM ( fact_transactions[amount] ),
    fact_transactions[real_fraud_label] = 1,
    fact_transactions[decision_status] <> "BLOCKED"
)
```
```dax
False Positive Cost = SUM ( fact_transactions[estimated_false_positive_cost] )
```
```dax
Total Estimated Cost = [Remaining Fraud Loss] + [False Positive Cost]
```
```dax
Net Estimated Saving = [Avoided Fraud Loss] - [False Positive Cost]
```
```dax
Savings Rate = DIVIDE ( [Net Estimated Saving], [Total Fraud Amount] )
```
```dax
-- Compares the live cost against a naive "block nothing" baseline,
-- where every simulated fraud amount would be lost.
Savings Compared to Threshold 0.50 =
VAR baseline_cost = [Total Fraud Amount]
RETURN baseline_cost - [Total Estimated Cost]
```

> For the **offline** model-level economics (default 0.50 vs cost-optimal) use the
> `fact_cost_analysis` table, which already contains `total_cost`,
> `savings_vs_default` and `is_optimal_threshold` per strategy.

---

## 4. Model analysis (from fact_model_benchmark)

```dax
Best Model =
CALCULATE (
    SELECTEDVALUE ( fact_model_benchmark[model_name] ),
    fact_model_benchmark[selected_best_model] = 1
)
```
```dax
Best Model F1 =
CALCULATE ( MAX ( fact_model_benchmark[f1] ), fact_model_benchmark[selected_best_model] = 1 )
```
```dax
Best Model MCC =
CALCULATE ( MAX ( fact_model_benchmark[mcc] ), fact_model_benchmark[selected_best_model] = 1 )
```
```dax
Best Model PR AUC =
CALCULATE ( MAX ( fact_model_benchmark[pr_auc] ), fact_model_benchmark[selected_best_model] = 1 )
```
```dax
Best Model Total Cost =
CALCULATE ( MAX ( fact_model_benchmark[total_estimated_cost] ), fact_model_benchmark[selected_best_model] = 1 )
```
```dax
Optimal Threshold =
CALCULATE ( MAX ( fact_cost_analysis[threshold_value] ), fact_cost_analysis[is_optimal_threshold] = 1 )
```
```dax
Default Threshold = 0.50
```
```dax
Default vs Optimal Saving =
CALCULATE ( MAX ( fact_cost_analysis[savings_vs_default] ), fact_cost_analysis[is_optimal_threshold] = 1 )
```

---

## 5. Time-based measures (near-real-time)

These use `NOW()`/`TODAY()`; both evaluate at refresh time and work in
DirectQuery. `created_at` is the row insertion timestamp.

```dax
Transactions Last Minute =
CALCULATE (
    [Total Transactions],
    FILTER ( fact_transactions, fact_transactions[created_at] >= NOW () - ( 1 / 1440 ) )
)
```
```dax
Frauds Last Minute =
CALCULATE (
    [Actual Simulated Frauds],
    FILTER ( fact_transactions, fact_transactions[created_at] >= NOW () - ( 1 / 1440 ) )
)
```
```dax
Alerts Last Minute =
CALCULATE (
    COUNTROWS ( fact_fraud_alerts ),
    FILTER ( fact_fraud_alerts, fact_fraud_alerts[timestamp] >= NOW () - ( 1 / 1440 ) )
)
```
```dax
Transactions Today =
CALCULATE (
    [Total Transactions],
    FILTER ( fact_transactions, fact_transactions[created_at] >= TODAY () )
)
```
```dax
Avoided Loss Today =
CALCULATE (
    [Avoided Fraud Loss],
    FILTER ( fact_transactions, fact_transactions[created_at] >= TODAY () )
)
```
```dax
Fraud Rate Rolling Window =
-- last 15 minutes
CALCULATE (
    [Fraud Rate],
    FILTER ( fact_transactions, fact_transactions[created_at] >= NOW () - ( 15 / 1440 ) )
)
```

---

## 6. Conditional-formatting helper (decision colour)

Use as the field-value rule on the live transactions table.

```dax
Decision Colour =
SWITCH (
    SELECTEDVALUE ( fact_transactions[decision_status] ),
    "APPROVED", "#22C55E",
    "BLOCKED", "#EF4444",
    "SUSPICIOUS", "#F59E0B",
    "REVIEW", "#F59E0B",
    "#94A3B8"
)
```
```dax
Risk Score Colour =
VAR s = SELECTEDVALUE ( fact_transactions[risk_score] )
RETURN SWITCH ( TRUE (), s >= 70, "#EF4444", s >= 45, "#F59E0B", "#22C55E" )
```
