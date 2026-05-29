# Power BI Integration — Fraud Detection Platform

This folder contains everything needed to build the interactive,
near-real-time Power BI dashboard **on top of the existing project**, without
changing any working component. The backend (views, endpoints, export, live
pipeline) is already wired; these are the design/spec/measure assets.

## Contents

| File | Purpose |
|------|---------|
| `fintech_fraud_theme.json` | Power BI report theme (dark FinTech/AI palette). |
| `dax_measures.md` | Ready-to-copy DAX for every KPI, mapped to real columns. |
| `data_dictionary.csv` | Every analytical column, its source and classification. |
| `star_schema.md` | Tables, relationships, conformed/generated dimensions. |
| `page_specifications.md` | Page-by-page spec for the 10 report pages. |
| `directquery_refresh_guide.md` | DirectQuery connection + auto page refresh. |
| `powerbi_integration_readme.md` | This file. |

## How the pieces fit (existing backend)

```
src/streaming/simulator.py   -> opens a SimulationRun, scores transactions,
                                 writes banking_transactions / banking_alerts /
                                 banking_shap_explanations (simulation_run_id tagged),
                                 finalises run metrics on stop
src/database/models.py       -> ORM incl. SimulationRun, ModelBenchmarkResult,
                                 CostComparisonSummary, CostAnalysisSweep, PowerBIExportLog
sql/powerbi_views_*.sql      -> vw_powerbi_* analytical views (Postgres + SQLite)
scripts/load_powerbi_warehouse.py -> load benchmark/cost CSVs into tables + apply views
src/api/routers/powerbi.py   -> /api/powerbi/* JSON fallback + /export-bundle
scripts/build_powerbi_bundle.py   -> timestamped CSV bundle + manifest (copies THIS folder)
```

The benchmark/cost facts originate from the precomputed thesis CSVs in
`reports/tables/` (`model_comparison.csv`, `cost_comparison_summary.csv`,
`cost_analysis_{model}.csv`). They are loaded read-only — the CSVs remain the
source of truth and are never overwritten.

## Quick start

### Option 1 — DirectQuery (recommended, near-real-time)
```bash
# 1. Point configs/config.yaml at PostgreSQL (see directquery_refresh_guide.md)
# 2. Create views + load warehouse tables (idempotent)
python scripts/load_powerbi_warehouse.py
# 3. Start the API + run a simulation from the website / banking router
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
# 4. Power BI Desktop -> Get Data -> PostgreSQL (DirectQuery) -> vw_powerbi_* views
#    Apply theme, add measures, turn on Automatic Page Refresh.
```

### Option 2 — Import-mode bundle (offline / no DB access)
```bash
python scripts/build_powerbi_bundle.py            # or: --limit 100000
# -> exports/powerbi_bundle/<timestamp>/ with all CSVs + this folder's assets + manifest.json
# Power BI Desktop -> Get Data -> Folder -> the timestamped directory.
```

### Option 3 — Web/JSON connector (live, no DB driver)
`Get Data -> Web -> http://<host>:8000/api/powerbi/transactions` (and the other
`/api/powerbi/*` endpoints listed in `directquery_refresh_guide.md §G`).

## Prerequisite data (so all pages populate)

- **Live pages (1–3, 10):** run the simulator at least once (creates a
  `simulation_runs` row and live transactions/alerts/SHAP).
- **Benchmark page (5):** `reports/tables/model_comparison.csv` (already present)
  → loaded by `load_powerbi_warehouse.py`.
- **Cost / threshold pages (4, 6, 7):** generate the cost CSVs first:
  ```bash
  python scripts/run_cost_analysis.py     # writes cost_comparison_summary.csv + cost_analysis_{model}.csv
  python scripts/load_powerbi_warehouse.py
  ```
  Until these exist, the cost/threshold views return 0 rows (the endpoints say
  so explicitly) — no error, just empty pages.

## Safety / non-regression guarantees

- **Additive only.** No existing route, table, model file, env var or frontend
  behaviour is renamed or removed. The Power BI router lives under the new
  `/api/powerbi` namespace; the views are read-only and never touch
  `banking_*`; the warehouse loader only TRUNCATEs the 3 analytic tables it owns.
- **No fabricated metrics.** Benchmark/cost numbers come from your computed CSVs;
  live KPIs come from real simulated transactions. `selected_best_model` is
  data-driven (cost when available, else MCC).
- **Honest labelling.** `data_dictionary.csv` classifies synthetic context vs
  model features vs SHAP output vs simulation ground truth. The Moroccan view
  carries a mandatory "synthetic demo" disclaimer.

## Regression test checklist

```bash
pytest -q                                   # existing suites still pass
curl http://localhost:8000/health           # core API up
curl http://localhost:8000/api/powerbi/views   # view row counts (503 = run loader)
python scripts/build_powerbi_bundle.py      # bundle builds; check manifest.json warnings
```
Confirm: simulation still runs; `/predict` still scores; benchmark CSV row count
== `vw_powerbi_model_benchmark` row count; SHAP join orphan count == 0.

## Rollback

- Drop the views: `DROP VIEW IF EXISTS vw_powerbi_*;` (no data lost — they are derived).
- Empty the analytic tables: re-run is idempotent, or `DELETE FROM model_benchmark_results;`
  (and `cost_comparison_summary`, `cost_analysis_sweep`).
- Remove the router: delete the `include_router(powerbi_router.router)` guard in
  `src/api/main.py` (it is already wrapped in try/except so a removal cannot
  break boot). None of this affects the live scoring path or the website.
