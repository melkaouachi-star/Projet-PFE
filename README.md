# Real-Time Credit-Card Fraud Detection - Master's Thesis Project

A **production-grade**, **publication-level** fraud-detection
platform combining advanced machine learning, real-time inference,
explainable AI (SHAP), ensemble learning, a REST API, a live
monitoring dashboard and a full MLOps deployment pipeline.

> **Use case:** simulate a real banking fraud-engine that detects
> fraudulent transactions in real time, blocks suspicious ones
> automatically and explains every decision to the user.

---

## Highlights

- End-to-end pipeline with **anti-leakage temporal validation**
  (`TimeSeriesSplit` + chronological hold-out).
- Benchmarks **Logistic Regression / Random Forest / XGBoost /
  LightGBM / CatBoost / Voting / Stacking** ensembles.
- Compares **eight class-imbalance strategies** including SMOTE,
  BorderlineSMOTE, ADASYN, SMOTEENN, Tomek Links and class weights.
- **Optuna-based Bayesian** hyper-parameter optimisation.
- **Probability calibration** + **business-cost threshold tuning**
  (configurable FP / FN costs).
- **SHAP** global, local, waterfall, beeswarm and dependence plots.
- **FastAPI** REST API with `/predict`, `/predict/batch`,
  `/explain`, `/predictions`, `/alerts`, `/stats`, `/health`.
- **Streamlit** monitoring dashboard with live tables, risk-score
  histograms and a built-in scoring + SHAP playground.
- **SQLAlchemy** ORM with SQLite (dev) / PostgreSQL (prod) backends.
- **Docker-compose** stack (API + Dashboard + Postgres).
- Deployment guides for **Render, Railway, HuggingFace Spaces, AWS**.

---

## Quick start

```bash
# 1. Install dependencies
#    Full stack (incl. PostgreSQL driver + MLflow):
pip install -r requirements.txt
#    OR - lighter dev install (SQLite-only, no Postgres, no MLflow):
pip install -r requirements-dev.txt

# 2. Download the dataset from Kaggle (mlg-ulb/creditcardfraud) into:
#    data/raw/creditcard.csv

# 3. Exploratory data analysis (publication-quality figures)
python scripts/run_eda.py

# 4. Train every enabled model (chronological CV + SMOTEENN by default)
python scripts/run_training.py

# 5. Generate the final comparison table, ROC/PR/threshold figures
python scripts/run_evaluation.py

# 6. Generate global + local SHAP plots
python scripts/run_shap.py

# 7. Start the API  (Swagger UI at http://localhost:8000/docs)
python scripts/run_api.py

# 8. In a second terminal, start the dashboard
python scripts/run_dashboard.py

# 9. Optional - replay live transactions against the API
python scripts/simulate_stream.py --n 200 --delay 0.3
```

---

## Project structure

```
.
├── configs/                # YAML configuration
├── data/                   # raw + processed datasets
├── docker/                 # Dockerfiles + docker-compose.yml
├── docs/                   # ARCHITECTURE.md, DEPLOYMENT.md, THESIS_DISCUSSION.md
├── models_store/           # serialised models, preprocessors, feature engineer
├── notebooks/              # exploratory notebooks (optional)
├── reports/
│   ├── figures/            # publication-quality PNGs
│   └── tables/             # CSV / JSON comparison tables
├── scripts/                # run_eda, run_training, run_evaluation, run_shap,
│                           # run_api, run_dashboard, simulate_stream
├── src/
│   ├── api/                # FastAPI app, schemas, routers, decision engine
│   ├── dashboard/          # Streamlit console
│   ├── data/               # loader, EDA, preprocessor
│   ├── database/           # SQLAlchemy models + CRUD
│   ├── evaluation/         # metrics + publication-quality plots
│   ├── explainability/     # SHAP layer (global + local + waterfall)
│   ├── features/           # engineering, imbalance, dimensionality reduction
│   ├── models/             # baseline, ensemble, calibration
│   ├── training/           # trainer, validation, Optuna, threshold
│   └── utils/              # config, logger, io
├── tests/                  # pytest unit tests
├── Makefile
├── README.md
└── requirements.txt
```

---

## REST API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/predict` | Score one transaction in real time |
| `POST` | `/api/v1/predict/batch` | Score a batch |
| `POST` | `/api/v1/explain` | Return SHAP decomposition |
| `GET`  | `/api/v1/predictions` | List recent predictions |
| `GET`  | `/api/v1/alerts` | List recent fraud alerts |
| `GET`  | `/api/v1/stats` | Aggregated counters |
| `GET`  | `/health` | Liveness probe |
| `GET`  | `/docs` | Swagger UI |

### Example - real-time scoring

**Request**

```http
POST /api/v1/predict
Content-Type: application/json

{
  "external_id": "tx-001",
  "Time": 12345.0,
  "Amount": 4900.0,
  "V14": -8.1,
  "V17": -9.4,
  "V12": -7.3
}
```

**Response**

```json
{
  "transaction_id": 42,
  "fraud_probability": 0.94,
  "risk_score": 92,
  "decision": "BLOCKED",
  "threshold": 0.85,
  "explanation": [
    "Unusually high transaction amount.",
    "Latent feature V14 strongly indicates fraudulent behaviour.",
    "Latent feature V17 deviates from legitimate-transaction patterns.",
    "Transaction occurred during high-risk hours."
  ],
  "model_name": "stacking_ensemble",
  "created_at": "2026-05-19T11:24:13.221Z"
}
```

---

## Dashboard

Run `python scripts/run_dashboard.py` and open
[http://localhost:8501](http://localhost:8501).

Four views are available:

1. **Live Monitoring** - real-time table of predictions, alerts,
   KPI cards (#blocked, #review, #alerts).
2. **Score a Transaction** - interactive form, posts to `/predict`,
   shows the decision + risk score + SHAP-derived explanation.
3. **SHAP Explainer** - synthetic transaction explorer with a
   horizontal SHAP bar chart.
4. **Analytics** - decisions over time, risk-score histograms,
   hourly fraud-rate breakdown.

---

## MLOps

- **Reproducibility:** fixed seeds, deterministic preprocessor /
  feature-engineer artefacts persisted in `models_store/`.
- **Logging:** structured loguru handlers, rotating file sink.
- **Configuration:** single `configs/config.yaml` consumed by every
  module through `src.utils.config.get_config()`.
- **Persistence:** every transaction + prediction + alert lands in
  SQLite or PostgreSQL with timestamped audit trail.
- **Deployment:** turnkey Dockerfiles + docker-compose with
  PostgreSQL. See `docs/DEPLOYMENT.md` for Render, Railway,
  HuggingFace Spaces and AWS recipes.
- **Optional MLflow tracking** via `MLFLOW_TRACKING_URI`.

---

## Thesis-ready outputs

- `reports/figures/` - 30+ publication-quality figures
  (class imbalance, KDE, temporal evolution, correlation,
  ROC, PR, threshold curves, confusion matrices, SHAP).
- `reports/tables/model_comparison.csv` - the final
  precision / recall / F1 / MCC / PR-AUC table.
- `reports/tables/training_summary.json` - artefact paths,
  training times and chosen thresholds per model.
- `docs/THESIS_DISCUSSION.md` - critical discussion of dataset bias,
  Moroccan vs European generalisation, ethical concerns and
  concept drift.

---

## Testing

```bash
pytest -q
```

---

## License

MIT - free for academic use.

## Citation

```bibtex
@mastersthesis{fraud_detection_2026,
  title  = {Real-Time Credit-Card Fraud Detection with Explainable AI},
  author = {<Your Name>},
  school = {<Your University>},
  year   = {2026}
}
```
