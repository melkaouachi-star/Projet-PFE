# Power BI Build Walkthrough — follow-along for the 20-step order

Companion to `page_specifications.md`. This file gives the **exact copy-paste
code** for every calculated column, dimension table, measure, and formatting
rule the build needs, reconciled to the **real** `vw_powerbi_*` columns and the
**real** data in the project's PostgreSQL `fraud_db`.

> Connection settings, SSL fix and Automatic Page Refresh: see
> `directquery_refresh_guide.md` (§B.1, §B.2, §C). Theme: apply
> `fintech_fraud_theme.json`. Star schema + relationships: `star_schema.md`.

## ⚠️ Read first — 3 reconciliations between the guide and the real data

1. **Decision values are `APPROVED` / `SUSPICIOUS` / `BLOCKED`.** The scoring
   engine does **not** emit `REVIEW`. `[Transactions Suspicious]` below counts
   both `SUSPICIOUS` and `REVIEW` so it is future-proof, but only `SUSPICIOUS`
   appears today. The `REVIEW = sky-blue` rule is harmless (it just never fires).
2. **`alert_status` does not exist.** `vw_powerbi_fraud_alerts` has no
   open/closed workflow column (there is no acknowledgement step in the model).
   So `[Alertes Ouvertes]` from §24 has no source — use `[Alertes Ouvertes] =
   [Nombre Alertes]` (every alert is effectively open) until/unless a real
   acknowledgement field is added. **Do not invent a status.**
3. **Moroccan map now has coordinates.** `vw_powerbi_moroccan_context` was
   extended with `latitude`, `longitude`, `fraud_rate` (averages of the
   synthetic coords), so the Page 9 map works as written. Re-run
   `python scripts/load_powerbi_warehouse.py --views-only` if you connected
   before this change.

---

## Steps 1–4 — Verify data + connect (DirectQuery)

```bash
# 1-2. Views exist and return rows (against fraud_db):
python scripts/load_powerbi_warehouse.py            # loads cost/benchmark + (re)creates views
curl http://localhost:8000/api/powerbi/views        # row counts per view
```
3–4. Power BI Desktop → Get Data → PostgreSQL → `localhost:5432` / `fraud_db`
(user `fraud`) → **DirectQuery** → select the nine `vw_powerbi_*` views +
`banking_customers`. (SSL error → `directquery_refresh_guide.md §B.2`.)

## Step 5 — Rename queries to star-schema names

| Connected view | Rename to |
|---|---|
| vw_powerbi_live_transactions | `fact_transactions` |
| vw_powerbi_fraud_alerts | `fact_fraud_alerts` |
| vw_powerbi_shap_explanations | `fact_shap` |
| vw_powerbi_model_benchmark | `fact_model_benchmark` |
| vw_powerbi_cost_comparison | `fact_cost_analysis` |
| vw_powerbi_threshold_optimization | `fact_threshold_optimization` |
| vw_powerbi_simulation_effectiveness | `fact_simulation` |
| vw_powerbi_moroccan_context | `dim_moroccan_context` |
| vw_powerbi_live_kpis | `live_kpis` |
| banking_customers | `dim_customer` |

## Step 6 — Fix column data types

On `fact_transactions`: `amount` → Decimal; `risk_score`, `real_fraud_label`,
`predicted_class` → Whole number; `fraud_probability`, `fraud_probability_pct`,
`latitude`, `longitude`, `estimated_avoided_loss`,
`estimated_false_positive_cost` → Decimal; `timestamp`, `created_at` →
Date/Time. On `dim_moroccan_context`: `latitude`, `longitude`, `fraud_rate` →
Decimal. On the benchmark/cost facts: metric columns → Decimal, count columns →
Whole number.

## Step 7 — Calculated columns on `fact_transactions`

> `transaction_hour` is now provided **by the view** (`vw_powerbi_live_transactions`,
> derived from `COALESCE(timestamp, created_at)`), so you do **not** need the
> calculated column below. After updating the view, do Home → **Transform Data**
> → Close & Apply once so DirectQuery picks up the new source column. The DAX
> version is kept only as a fallback if you prefer a model-side column:

```dax
transaction_hour =
IF ( ISBLANK ( fact_transactions[timestamp] ), BLANK (), HOUR ( fact_transactions[timestamp] ) )
```
```dax
Transaction Date =
IF (
    ISBLANK ( fact_transactions[timestamp] ),
    BLANK (),
    DATE ( YEAR ( fact_transactions[timestamp] ), MONTH ( fact_transactions[timestamp] ), DAY ( fact_transactions[timestamp] ) )
)
```
```dax
Risk Band =
SWITCH (
    TRUE (),
    fact_transactions[risk_score] >= 70, "High",
    fact_transactions[risk_score] >= 45, "Watch",
    "Low"
)
```

## Step 8 — Dimension tables (New table)

```dax
dim_date =
ADDCOLUMNS (
    CALENDAR ( MIN ( fact_transactions[timestamp] ), MAX ( fact_transactions[timestamp] ) ),
    "Year", YEAR ( [Date] ),
    "MonthNo", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Day", DAY ( [Date] ),
    "Weekday", FORMAT ( [Date], "ddd" ),
    "YearMonth", FORMAT ( [Date], "YYYY-MM" )
)
```
Then Table tools → **Mark as date table** → `[Date]`.

```dax
dim_decision_status =
DATATABLE (
    "decision_status", STRING,
    "sort_order", INTEGER,
    "color", STRING,
    {
        { "APPROVED",   1, "#22C55E" },
        { "SUSPICIOUS", 2, "#F59E0B" },
        { "REVIEW",     3, "#7DD3FC" },
        { "BLOCKED",    4, "#EF4444" }
    }
)
```
```dax
dim_risk_level =
DATATABLE (
    "Risk Band", STRING,
    "min_score", INTEGER,
    "max_score", INTEGER,
    "sort_order", INTEGER,
    "color", STRING,
    {
        { "Low",   0,  44, 1, "#22C55E" },
        { "Watch", 45, 69, 2, "#F59E0B" },
        { "High",  70, 100, 3, "#EF4444" }
    }
)
```
Sort `decision_status` by `sort_order` and `Risk Band` by `sort_order`
(Column tools → Sort by column).

## Step 9 — Relationships (single-direction, one-to-many)

| One side | Many side |
|---|---|
| `dim_date[Date]` | `fact_transactions[Transaction Date]` |
| `dim_decision_status[decision_status]` | `fact_transactions[decision_status]` |
| `dim_risk_level[Risk Band]` | `fact_transactions[Risk Band]` |
| `dim_customer[customer_id]` | `fact_transactions[customer_id]` |
| `dim_customer[customer_id]` | `fact_fraud_alerts[customer_id]` |
| `fact_transactions[transaction_id]` | `fact_fraud_alerts[transaction_id]` |
| `fact_transactions[transaction_id]` | `fact_shap[transaction_id]` |

Leave `fact_model_benchmark`, `fact_cost_analysis`,
`fact_threshold_optimization`, `fact_simulation`, `dim_moroccan_context`,
`live_kpis` **unrelated** (different grain — filter with their own slicers).
This is what prevents the SHAP double-count (§38).

## Step 10 — Measures (names match the guide; host on a `_Measures` table)

These use the guide's page-build names. (`dax_measures.md` is the full library
with English names + time/economic/model measures — both are valid; pick one
convention and stay consistent.)

```dax
Total Transactions = COUNTROWS ( fact_transactions )
```
```dax
Transactions Approved = CALCULATE ( [Total Transactions], fact_transactions[decision_status] = "APPROVED" )
```
```dax
Transactions Blocked = CALCULATE ( [Total Transactions], fact_transactions[decision_status] = "BLOCKED" )
```
```dax
Transactions Suspicious =
CALCULATE ( [Total Transactions], fact_transactions[decision_status] IN { "SUSPICIOUS", "REVIEW" } )
```
```dax
Fraud Rate = DIVIDE ( CALCULATE ( [Total Transactions], fact_transactions[real_fraud_label] = 1 ), [Total Transactions] )
```
```dax
Montant Total = SUM ( fact_transactions[amount] )
```
```dax
Montant Total Fraudes = CALCULATE ( SUM ( fact_transactions[amount] ), fact_transactions[real_fraud_label] = 1 )
```
```dax
Pertes Évitées = SUM ( fact_transactions[estimated_avoided_loss] )
```
```dax
Taux de Pertes Évitées = DIVIDE ( [Pertes Évitées], [Montant Total Fraudes] )
```
```dax
Nombre Alertes = COUNTROWS ( fact_fraud_alerts )
```
```dax
-- No acknowledgement workflow exists yet -> every alert is "open".
Alertes Ouvertes = [Nombre Alertes]
```

For Precision / Recall / F1 / confusion matrix / economic / best-model / time
measures, copy them verbatim from `dax_measures.md` (§2–§5). They reference the
same real columns.

## Steps 11–15 — Build the pages

Full per-page layout, visuals and field bindings are in
`page_specifications.md` (Pages 1–10). Key bindings recap:

- **Page 1 (exec):** KPI cards → the Step-10 measures; donut legend
  `fact_transactions[decision_status]`; line `[Total Transactions]` by
  `dim_date[Date]` / `transaction_hour`, legend `decision_status`; gauge
  `[Fraud Rate]` max `0.10`; map by `city` or `latitude`/`longitude`.
- **Page 2 (transactions):** table of `transaction_id, timestamp, customer_id,
  amount, decision_status, risk_score, Risk Band, city, model_name` +
  conditional formatting (below).
- **Page 3 (alerts):** `fact_fraud_alerts` — `[Nombre Alertes]`, alerts by
  `transaction_hour`, by `Risk Band`, by `city`, critical list (`severity`).
- **Page 4 (cost):** `[Montant Total]`, `[Montant Total Fraudes]`,
  `[Pertes Évitées]`, `[Taux de Pertes Évitées]` + waterfall (fraud amount →
  blocked → residual). 28 `fact_cost_analysis` rows available.
- **Page 5 (benchmark):** `fact_model_benchmark` (7 models) — do **not** cross
  with live transactions (§ methodological note).
- **Pages 6–7 (cost/threshold):** `fact_cost_analysis` (28 rows) /
  `fact_threshold_optimization` (693 rows). Use `is_cost_optimal`,
  `is_f1_optimal`, `is_mcc_optimal` for reference lines.
- **Page 8 (SHAP):** `fact_shap` — bar `shap_value` by `feature_name`; keep
  `shap_output` and `business_wording` visually separate (§39).
- **Page 9 (Morocco):** `dim_moroccan_context` map — Lat=`latitude`,
  Long=`longitude`, bubble size=`transactions`, colour=`fraud_rate`,
  tooltip=`city`,`total_amount`,`fraud_rate`; **paste the `data_label`
  disclaimer in a visible text box.**

### Conditional formatting (Page 2 table) — Step 23

Add this measure, then on each relevant column: Format → Cell elements →
Background/Font colour → Format by **Field value** → `[Decision Colour]`.

```dax
Decision Colour =
SWITCH (
    SELECTEDVALUE ( fact_transactions[decision_status] ),
    "APPROVED",   "#22C55E",
    "SUSPICIOUS", "#F59E0B",
    "REVIEW",     "#7DD3FC",
    "BLOCKED",    "#EF4444",
    "#94A3B8"
)
```
```dax
Risk Score Colour =
VAR s = SELECTEDVALUE ( fact_transactions[risk_score] )
RETURN SWITCH ( TRUE (), s >= 70, "#EF4444", s >= 45, "#F59E0B", "#22C55E" )
```

## Step 16 — FinTech theme

View → Themes → Browse → `powerbi/fintech_fraud_theme.json`. (Palette already
encodes background `#07111F`, panels, AI cyan `#38BDF8`, and the
approved/suspicious/blocked risk colours. You can keep the guide's
`#0F1E33`/`#123B72` panel/blue if you prefer — edit `dataColors`/`background`
in the JSON.)

## Step 17 — Automatic Page Refresh

Pages 1–3 (live): Format → Page refresh → On → 5 s. Leave Pages 4–9 off (static
benchmark/cost/SHAP/Morocco). Details + Service caveats: `directquery_refresh_guide.md §C–D`.

## Step 18 — Live test (while a simulation runs)

| Simulation action | Expected in Power BI (after refresh) |
|---|---|
| New approved tx | `[Total Transactions]` ↑, `[Transactions Approved]` ↑ |
| Suspicious tx | `[Transactions Suspicious]` ↑ |
| Blocked fraud | `[Transactions Blocked]` ↑, `[Pertes Évitées]` ↑ |
| New alert | Page 3 list grows |
| New SHAP | transaction visible on Page 8 |

## Steps 19–20 — Publish + final check

Publish → workspace → in the Service: Settings → **Gateway/data source
connections** → enter DB credentials → (on-prem gateway if `fraud_db` is
private) → confirm DirectQuery works. Then the pre-defense checklist below.

---

## Pre-defense checklist (§38–§40)

- **No double counting:** `fact_transactions` and `fact_shap` stay separate,
  joined on `transaction_id` (Step 9). Verify `[Total Transactions]` equals the
  DB count, not count × SHAP features.
- **Classification visible:** show the `classification` legend from
  `data_dictionary.csv` (`real_simulated`, `model_output`, `shap_output`,
  `business_wording`, `synthetic_context`, `simulation_ground_truth`,
  `synthetic_demo`).
- **KPIs working:** Total / Approved / Suspicious / Blocked / Fraud Rate /
  Montant Total / Pertes Évitées / Taux de Pertes Évitées / Precision / Recall /
  F1 / benchmark / cost / optimal threshold / SHAP / Morocco-with-disclaimer.
- **Honest labels:** Morocco page carries the `data_label`; `real_fraud_label`
  noted as simulation-only ground truth.
