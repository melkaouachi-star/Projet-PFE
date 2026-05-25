# ============================================================
# Railway/FastAPI backend image
# ============================================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENABLE_SHAP=0 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
COPY models_store ./models_store

EXPOSE 8080
CMD ["python", "scripts/run_api.py"]
