# Power BI Star Schema — FinTech Fraud Detection

This is the analytical model Power BI builds on top of the read-only
`vw_powerbi_*` views. Nothing here changes the live `banking_*` tables.

## Connecting the sources

Each Power BI query maps 1:1 to a view (or a base table for the customer
dimension). Rename the query to the **table name** in the left column below.

| Power BI table              | Source                                   | Grain                              |
|-----------------------------|------------------------------------------|------------------------------------|
| `fact_transactions`         | `vw_powerbi_live_transactions`           | one row per transaction            |
| `fact_fraud_alerts`         | `vw_powerbi_fraud_alerts`                | one row per alert                  |
| `fact_shap`                 | `vw_powerbi_shap_explanations`           | one row per (transaction, feature) |
| `fact_model_benchmark`      | `vw_powerbi_model_benchmark`             | one row per model                  |
| `fact_cost_analysis`        | `vw_powerbi_cost_comparison`             | one row per (model, strategy)      |
| `fact_threshold_optimization` | `vw_powerbi_threshold_optimization`    | one row per (model, threshold)     |
| `fact_simulation`           | `vw_powerbi_simulation_effectiveness`    | one row per simulation run         |
| `dim_customer`              | `banking_customers`                      | one row per customer               |
| `dim_moroccan_context`      | `vw_powerbi_moroccan_context`            | one row per Moroccan city (demo)   |
| `live_kpis`                 | `vw_powerbi_live_kpis`                   | single-row KPI snapshot            |

## Generated (calculated) dimensions

Create these **in Power BI** — they are not views (keeps the DB lean):

* `dim_date` — `CALENDAR ( MIN(fact_transactions[timestamp]), MAX(fact_transactions[timestamp]) )`
  plus Year/Month/Day/Weekday columns. Mark as date table.
* `dim_time` — one row per minute or per hour bucket, joined on the hour/minute
  extracted from `fact_transactions[timestamp]`.
* `dim_decision_status` — Enter Data: APPROVED / SUSPICIOUS / REVIEW / BLOCKED,
  with a sort order and a colour hex (drives the legend ordering).
* `dim_risk_level` — Enter Data: Low (0–44) / Watch (45–69) / High (70–100),
  joined to a `Risk Band` calculated column on `fact_transactions`.

`dim_location`, `dim_model` and `dim_simulation_run` are **conceptual** — they
are already denormalised inside the fact views (`country`/`city`/`lat`/`lon`,
`model_name`, `simulation_run_id`). Use them as fields directly, or split them
into their own Enter-Data/derived tables only if you need cross-fact filtering.

## Relationships

All relationships are **single-direction, one-to-many** (the "1" side is the
dimension). This avoids ambiguous many-to-many paths.

```
dim_customer (1) ───< (─) fact_transactions[customer_id]
dim_customer (1) ───< (─) fact_fraud_alerts[customer_id]

fact_transactions (1) ───< (─) fact_fraud_alerts[transaction_id]
fact_transactions (1) ───< (─) fact_shap[transaction_id]

dim_date (1) ───< (─) fact_transactions[transaction_date]   (or timestamp→date)
dim_simulation_run* (1) ───< (─) fact_transactions[simulation_run_id]
        (*use fact_simulation as the run dimension; relate on simulation_run_id)

dim_decision_status (1) ───< (─) fact_transactions[decision_status]
dim_risk_level (1) ───< (─) fact_transactions[Risk Band]
```

The benchmark / cost / threshold facts are **independent analytical tables**.
Relate them to each other on `model_name` only if you build a `dim_model`
bridge; otherwise filter them with their own slicers. They are NOT joined to
`fact_transactions` (different grain: offline test set vs live simulation).

`live_kpis` is a disconnected single-row helper; surface it with card visuals
directly (do not relate it).

## Why this shape

* **One fact per grain.** Transactions, alerts and SHAP features have different
  grains, so they are separate facts joined through `transaction_id`, never
  flattened — this keeps `Total Transactions` from double-counting.
* **Conformed dimensions.** `dim_customer`, `dim_date` and `dim_decision_status`
  filter multiple facts consistently.
* **Offline vs live separation.** The European-dataset benchmark/cost facts are
  kept apart from the live simulation facts because they describe different
  populations. Mixing them in one relationship would produce misleading totals.

## Classification of fields (for honest reporting)

`powerbi/data_dictionary.csv` tags every column with a `classification`:

* `real_simulated` — produced by the live simulation pipeline.
* `model_output` — produced by the scoring engine.
* `shap_output` / `business_wording` — SHAP contributions vs the human phrasing
  derived from them (keep these visually distinct on Page 8).
* `synthetic_context` — geographic / identity / merchant fields synthesised for
  the demo. **These were NOT features of the trained European model.**
* `simulation_ground_truth` — `real_fraud_label`, available only because this is
  a simulation.
* `synthetic_demo` — the Moroccan-context demo (carry the disclaimer label).
