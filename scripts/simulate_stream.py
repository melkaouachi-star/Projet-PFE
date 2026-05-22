"""
Stream simulator - replays the dataset against the running API.

Useful for live demos & dashboard population.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.config import PROJECT_ROOT, get_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200, help="Number of transactions to replay.")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between transactions.")
    parser.add_argument("--fraud_ratio", type=float, default=0.1,
                        help="Fraction of injected frauds in the replay.")
    args = parser.parse_args()

    cfg = get_config()
    csv = PROJECT_ROOT / cfg.paths.data_raw
    if not csv.exists():
        raise FileNotFoundError(f"Place creditcard.csv at {csv}")
    df = pd.read_csv(csv)

    fraud = df[df["Class"] == 1].sample(int(args.n * args.fraud_ratio), random_state=42)
    legit = df[df["Class"] == 0].sample(args.n - len(fraud), random_state=42)
    sample = pd.concat([fraud, legit]).sample(frac=1, random_state=1).reset_index(drop=True)

    url = f"http://{cfg.api.host}:{cfg.api.port}/api/v1/predict"
    for i, row in sample.iterrows():
        payload = row.drop("Class").to_dict()
        payload["external_id"] = f"stream-{i:05d}"
        try:
            r = requests.post(url, json=payload, timeout=5).json()
            print(f"#{i:04d} -> {r.get('decision'):<8}  p={r.get('fraud_probability'):.4f}  "
                  f"risk={r.get('risk_score')}")
        except Exception as exc:
            print(f"#{i:04d}  ERROR: {exc}")
        time.sleep(args.delay)


if __name__ == "__main__":
    main()
