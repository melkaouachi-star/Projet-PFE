# Enterprise Fraud Detection Platform - Functional Spec

## 1. Capabilities

| Capability                       | Module / Endpoint |
|----------------------------------|-------------------|
| Real-time scoring                | `POST /api/v1/predict` + `FraudDecisionEngine` |
| Dynamic fraud probability        | `src/scoring/dynamic_scorer.py` (ML + rule overlay) |
| Risk score 0-100 & fraud level   | `EngineDecision.risk_score`, `fraud_level` |
| Auto-block decisions             | `block_threshold` (configurable) -> `Decision.BLOCKED` |
| Explainable decisions            | SHAP + rule contributions -> `DecisionOut.explanation` |
| Live transaction stream          | `WS /ws/stream`, `GET /sse/stream` |
| Synthetic customer generation    | `POST /api/v1/customers/seed`, `seed_customers.py` |
| 10/100/1000 tps simulator        | `POST /api/v1/simulation/start` (rate_tps configurable) |
| 10 fraud scenarios               | `src/simulation/fraud_scenarios.py` |
| Live monitoring                  | dashboard - Overview / Live Map / Alerts |
| Geographic visualisation         | Leaflet (`folium`) map page |
| Fraud alert center               | `GET /api/v1/fraud-alerts`, ack workflow |
| Country breakdown                | `GET /api/v1/country-breakdown` |
| KPI counters                     | `GET /api/v1/stats` |
| Production logging / config      | loguru + YAML + `.env` |

## 2. Fraud Scenarios

1. High-amount transaction
2. Night transaction (00-06 / 22-24)
3. Foreign country transaction
4. Impossible travel (>800 km/h)
5. Rapid transaction bursts (card testing)
6. Stolen card behaviour (several mid-amount in a new city)
7. Bot-generated fraud (same IP / browser / device)
8. Multi-IP fraud
9. Account takeover (probe + large transfer)
10. Anomalous spending pattern

Each scenario produces a `GeneratedTransaction` (or several) with realistic
banking attributes - country, city, lat/lon, IP, browser, OS, payment
method, card type, merchant.

## 3. Dynamic Fraud Scoring

`final_probability = (1 - rule_blend) * ML_probability + rule_blend * rule_score`

Default `rule_blend = 0.45`.

### Rule overlay

| Code               | Weight | Trigger |
|--------------------|--------|---------|
| AMT_OUTLIER        | 0.20   | amount > 10x customer baseline (and > 200) |
| AMT_VERY_HIGH      | 0.15   | amount >= 10,000 |
| NIGHT              | 0.10   | hour < 6 or hour >= 22 |
| HIGH_RISK_GEO      | 0.18   | originating from a high-risk country |
| MED_RISK_GEO       | 0.08   | originating from a medium-risk country |
| VELOCITY           | 0.15   | >5 transactions in last 60 s for this customer |
| IMPOSSIBLE_TRAVEL  | 0.25   | distance / elapsed > 800 km/h |
| MULTI_IP           | 0.10   | >=4 distinct IPs in last 10 events |
| FRAUDSTER          | 0.15   | customer.risk_category == FRAUDSTER |
| FOREIGN            | 0.08   | tx_country != customer_country |

### Fraud levels

| Risk score | Level    |
|------------|----------|
| 0-39       | LOW      |
| 40-69      | MEDIUM   |
| 70-89      | HIGH     |
| 90-100     | CRITICAL |

### Decision bands

| Final probability | Decision  |
|-------------------|-----------|
| < 0.50            | APPROVED  |
| 0.50 - 0.85       | REVIEW    |
| >= 0.85           | BLOCKED   |

## 4. WebSocket payload

```json
{
  "type": "transaction",
  "transaction_id": 1842,
  "external_id": "TX-...",
  "timestamp": "2026-05-20T15:24:01.221Z",
  "customer_id": "CUST-000123-A1B2C3",
  "customer_name": "Yasmine El Amrani",
  "amount": 4900.0, "currency": "EUR",
  "country": "Russia", "city": "Moscow",
  "latitude": 55.7558, "longitude": 37.6173,
  "ip_address": "188.45.71.10",
  "merchant_name": "ATM Withdrawal",
  "fraud_probability": 0.94, "base_ml_probability": 0.81,
  "risk_score": 95, "fraud_level": "CRITICAL", "decision": "BLOCKED",
  "explanation": [
    "Very large absolute amount (>10,000).",
    "Originated from a high-risk country.",
    "Transaction occurred during high-risk hours."
  ],
  "scenario": "stolen_card"
}
```

## 5. Operating the platform

```bash
# 1. Install
pip install -r requirements-dev.txt

# 2. Train baseline models
python scripts/run_training.py

# 3. Start the API (loads models + opens DB + lifts WebSocket)
python scripts/run_api.py

# 4. Seed customers and open the integrated dashboard
python scripts/seed_customers.py --n 500
# Dashboard: http://localhost:8000/dashboard

# 5. Drive the simulator from CLI (or from the Simulation Lab page)
python scripts/run_simulator.py --rate 100 --fraud-ratio 0.08
python scripts/run_simulator.py --stop
```
