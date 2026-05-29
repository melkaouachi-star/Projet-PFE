# DirectQuery & Near-Real-Time Refresh Guide

The canonical near-real-time path is **Power BI DirectQuery → the
`vw_powerbi_*` PostgreSQL views**. Import mode (CSV/API bundle) is the fallback.

```
Website simulation bot
  → FastAPI backend (src/api, src/streaming/simulator.py)
  → PostgreSQL  (banking_transactions / banking_alerts / banking_shap_explanations
                 / simulation_runs + the loaded benchmark/cost tables)
  → SQL views   (sql/powerbi_views_postgres.sql)
  → Power BI DirectQuery
  → Automatic page refresh
```

## A. One-time setup

1. **Use PostgreSQL for live work.** SQLite (the default `fraud_detection.db`)
   has **no DirectQuery connector** — it is for local Import-mode testing only.
   Point the app at Postgres in `configs/config.yaml` (or `DATABASE_URL`):
   ```yaml
   database:
     url: "postgresql+psycopg2://user:pass@host:5432/fraud_db"
   ```
2. **Create the views + load the warehouse tables:**
   ```bash
   python scripts/load_powerbi_warehouse.py
   ```
   This loads the benchmark/cost CSVs into tables and runs
   `sql/powerbi_views_postgres.sql` (auto-detected by dialect). Re-runnable and
   idempotent (it TRUNCATEs then reloads — never duplicates).
3. **Verify the views exist** (any one of):
   ```bash
   psql "$DATABASE_URL" -c "\dv vw_powerbi_*"
   curl http://localhost:8000/api/powerbi/views      # row counts per view
   ```

## B. Connect Power BI Desktop (DirectQuery)

1. Home → Get Data → **PostgreSQL database**. Enter server & database.
2. **Data Connectivity mode → DirectQuery.**
3. Select the nine `vw_powerbi_*` views and `banking_customers`.
4. Rename each query to its star-schema name (see `powerbi/star_schema.md`).
5. Build relationships per `star_schema.md` (single-direction, one-to-many).
6. Apply the theme: View → Themes → Browse → `powerbi/fintech_fraud_theme.json`.
7. Add the measures from `powerbi/dax_measures.md` (host them on a `_Measures` table).

## C. Automatic page refresh (near-real-time)

DirectQuery supports **Automatic Page Refresh (APR)**:

1. Click an empty area of the page → Format pane → **Page refresh**.
2. Toggle **On**, set interval (e.g. **5 seconds** — matches
   `configs/config.yaml → dashboard.refresh_interval_seconds`).
3. Repeat for Page 1, 2, 3, 10 (the live pages). Leave benchmark/cost pages
   (5–9) without APR — that data is static.

> The admin "minimum refresh interval" applies in the Power BI Service. In
> Desktop you can set any interval ≥ 1s. Keep ≥ 5s to avoid hammering Postgres.

## D. Power BI Service (optional, scheduled)

For Import-mode datasets published to the Service, configure a **Scheduled
refresh** (up to 8×/day on Pro, 48×/day on Premium) via an **On-premises data
gateway** if Postgres is private. DirectQuery datasets refresh visuals live and
need a gateway only for the cloud Service to reach the database.

## E. Indexes for live analytics (already in the model)

`src/database/models.py` indexes the columns Power BI filters on:
`banking_transactions`: `simulation_run_id`, `country`, `merchant_category`,
`risk_score`, `decision`, `timestamp`, `created_at`; `banking_alerts`:
`severity`, `created_at`. No extra migration is required. If you add heavy
date-range pages, consider a composite index:
```sql
CREATE INDEX IF NOT EXISTS ix_bt_run_created
  ON banking_transactions (simulation_run_id, created_at);
```

## F. Test queries

```sql
SELECT COUNT(*) FROM vw_powerbi_live_transactions;
SELECT * FROM vw_powerbi_live_kpis;
SELECT model_name, model_rank, selected_best_model
  FROM vw_powerbi_model_benchmark ORDER BY model_rank;
-- joinability: SHAP rows must reference existing transactions
SELECT COUNT(*) AS orphan_shap
FROM vw_powerbi_shap_explanations s
LEFT JOIN vw_powerbi_live_transactions t USING (transaction_id)
WHERE t.transaction_id IS NULL;   -- expect 0
```

## G. Fallback: Import via the JSON API or CSV bundle

When a direct DB connection is unavailable:
- **Web connector:** Get Data → Web → `http://<host>:8000/api/powerbi/transactions`
  (and `/kpis`, `/fraud-alerts`, `/shap-explanations`, `/model-benchmark`,
  `/cost-summary`, `/threshold-optimization/{model}`, `/simulation-summary`).
  These return the same view data as JSON.
- **CSV bundle:** `python scripts/build_powerbi_bundle.py` →
  `exports/powerbi_bundle/<timestamp>/` → Get Data → Folder/Text.
  Import mode means you re-import (or schedule refresh) instead of live APR.
