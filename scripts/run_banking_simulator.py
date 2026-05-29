"""CLI fraud bot for realistic banking transaction streams."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulation.customers import CustomerGenerator  # noqa: E402
from src.simulation.transactions import TransactionGenerator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic banking transactions against the API.")
    parser.add_argument("--api", default="http://localhost:8000", help="FastAPI base URL.")
    parser.add_argument("--rate", type=int, default=10, choices=[10, 100, 1000], help="Transactions per second.")
    parser.add_argument("--n", type=int, default=250, help="Number of transactions to send.")
    parser.add_argument("--fraud-ratio", type=float, default=0.08, help="Injected fraud scenario ratio.")
    parser.add_argument("--customers", type=int, default=5000, help="Synthetic customer population size.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    customers = CustomerGenerator(seed=args.seed).generate_many(args.customers)
    generator = TransactionGenerator(seed=args.seed, customers=customers)
    interval = 1 / args.rate
    url = f"{args.api.rstrip('/')}/predict"

    print(f"Streaming {args.n} banking transactions to {url} at {args.rate} TPS")
    started = time.perf_counter()
    for i in range(args.n):
        tx = generator.generate_transaction(rate_tps=args.rate, fraud_ratio=args.fraud_ratio)
        try:
            res = requests.post(url, json=tx, timeout=10)
            res.raise_for_status()
            scored = res.json()
            print(
                f"{i + 1:06d} {scored['decision']:<10} "
                f"risk={scored['risk_score']:>3} "
                f"p={scored['fraud_probability']:>5.1f}% "
                f"{tx['customer_name']} {tx['transaction_currency']} {tx['transaction_amount']:,.2f}"
            )
        except Exception as exc:
            print(f"{i + 1:06d} ERROR {exc}")
        elapsed_target = (i + 1) * interval
        sleep_for = elapsed_target - (time.perf_counter() - started)
        if sleep_for > 0:
            time.sleep(sleep_for)


if __name__ == "__main__":
    main()

