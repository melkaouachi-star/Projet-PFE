# Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  Real-time Fraud Detection                    │
└───────────────────────────────────────────────────────────────┘

                ┌─────────────────────┐
                │ Streamlit Dashboard │
                │  - Live monitoring  │
                │  - SHAP viewer      │
                │  - Analytics        │
                └────────┬────────────┘
                         │ HTTPS
                         ▼
                ┌─────────────────────┐
                │   FastAPI Backend   │
   Transaction  │ /predict            │
 ─────────────► │ /predict/batch      │
                │ /explain            │
                │ /predictions /stats │
                │ /alerts /health     │
                └────┬───────┬────────┘
                     │       │
            ┌────────▼┐   ┌──▼────────────────────────┐
            │ Engine  │   │ SQLAlchemy ORM            │
            │ - FE    │   │  - Transactions           │
            │ - Scale │   │  - Predictions            │
            │ - Model │   │  - FraudAlerts            │
            │ - SHAP  │   └─────────────┬─────────────┘
            └────┬────┘                 ▼
                 │           ┌────────────────────────┐
                 │           │  SQLite / PostgreSQL    │
                 ▼           └────────────────────────┘
        ┌──────────────────┐
        │ models_store/    │
        │  preprocessor.pkl│
        │  feature_eng.pkl │
        │  *.pkl ensembles │
        └──────────────────┘

Offline pipeline (scripts/):
  run_eda  ─►  run_training  ─►  run_evaluation  ─►  run_shap
                    │
                    └─ Optuna tuning (--tune)
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `src/data` | dataset loading, schema validation, EDA, preprocessing |
| `src/features` | advanced feature engineering, imbalance handling, dimensionality reduction |
| `src/models` | baseline + ensemble + stacking model factories, probability calibration |
| `src/training` | training pipeline, Optuna optimizer, anti-leakage validation, threshold tuning |
| `src/evaluation` | metrics, ROC/PR/threshold/confusion-matrix figures, comparison tables |
| `src/explainability` | SHAP explainer (global + local + waterfall + API helper) |
| `src/database` | SQLAlchemy ORM, sessions, CRUD |
| `src/api` | FastAPI app, schemas, routers, real-time decision engine |
| `src/api/static/dashboard.html` | Integrated live dashboard served by FastAPI at `/dashboard` |
| `src/utils` | config loader, logger, IO helpers |
