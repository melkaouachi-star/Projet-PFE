# =====================================================================
# Make targets - convenience wrappers for the most common commands.
# =====================================================================

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements.txt

eda:
	$(PYTHON) scripts/run_eda.py

train:
	$(PYTHON) scripts/run_training.py

train-tune:
	$(PYTHON) scripts/run_training.py --tune

evaluate:
	$(PYTHON) scripts/run_evaluation.py

shap:
	$(PYTHON) scripts/run_shap.py

api:
	$(PYTHON) scripts/run_api.py

dashboard:
	$(PYTHON) scripts/run_dashboard.py

stream-demo:
	$(PYTHON) scripts/simulate_stream.py --n 100 --delay 0.3 --fraud_ratio 0.15

test:
	pytest -q --maxfail=1 --disable-warnings

docker-up:
	docker compose -f docker/docker-compose.yml up --build

docker-down:
	docker compose -f docker/docker-compose.yml down -v
