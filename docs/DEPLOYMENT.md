# Deployment guide

The project is **container-native** and ships with a docker-compose
file that boots the API, the dashboard and a PostgreSQL database in
one command.  Below are platform-specific guides for the four most
common targets.

---

## 1. Local

```bash
pip install -r requirements.txt
# Download the dataset from https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
# and copy it to data/raw/creditcard.csv
python scripts/run_training.py
python scripts/run_evaluation.py
python scripts/run_api.py            # http://localhost:8000/docs
python scripts/run_dashboard.py      # http://localhost:8501
```

## 2. Docker Compose (recommended)

```bash
# Train once, locally, so the model artefacts exist:
python scripts/run_training.py
# Then start every service:
docker compose -f docker/docker-compose.yml up --build
```

## 3. Render

1. Push the repo to GitHub.
2. Create two **Web Services** on Render:
   - **API**: `docker/Dockerfile.api`. It binds to Render's `PORT`
     environment variable, defaulting to `10000`.
   - **Dashboard**: `docker/Dockerfile.dashboard`, port `8501`,
     env var `DASHBOARD_API_BASE_URL=https://<api-service>.onrender.com`.
3. Provision a **Render PostgreSQL** instance and set
   `DATABASE_URL` on the API service.

## 4. Railway

The API service is configured by `railway.json` to build
`docker/Dockerfile.api`, install the lightweight `requirements-api.txt`
runtime dependencies, start Uvicorn on Railway's `PORT`, and use
`/health` as the deployment healthcheck. Provision a Postgres plugin
and inject its connection URL into the API service when you want
persistent monitoring data.

## 5. HuggingFace Spaces

For a fully-managed *demo* deployment:

- Type: `Streamlit`
- App file: `src/dashboard/app.py`
- Hardware: `CPU basic`
- Set the secret `DASHBOARD_API_BASE_URL` to your API's public URL.

The API itself can run on a separate Space using
`type: docker` and `Dockerfile.api`.

## 6. AWS

- Build & push the two images to ECR.
- API: deploy on **ECS Fargate** behind an ALB.
- Dashboard: deploy on **App Runner**.
- Database: **RDS PostgreSQL**.
- Static figures + model artefacts: store in **S3** and mount them
  via `models_store/` at startup.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy connection string (SQLite default) |
| `API_HOST`, `API_PORT` | API binding |
| `DASHBOARD_API_BASE_URL` | URL the dashboard uses to call the API |
| `FRAUD_CONFIG` | Override path to `configs/config.yaml` |
| `LOG_LEVEL` | DEBUG / INFO / WARNING |
