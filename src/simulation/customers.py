"""Synthetic customer generator for banking fraud simulations."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from src.simulation.catalogs import (
    BEHAVIOR_PATTERNS,
    COUNTRY_CITIES,
    FIRST_NAMES,
    LAST_NAMES,
)


@dataclass
class CustomerGenerator:
    seed: int = 42

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def generate_customer(self, index: int) -> dict[str, Any]:
        risk_profile = self.rng.choices(
            ["LOW", "MEDIUM", "VIP", "HIGH", "FRAUDSTER"],
            weights=[54, 24, 12, 8, 2],
            k=1,
        )[0]
        country = self.rng.choice(list(COUNTRY_CITIES.keys()))
        city, lat, lon = self.rng.choice(COUNTRY_CITIES[country])
        behavior = self._behavior_for_profile(risk_profile)
        avg_spend = self._average_spend(risk_profile)
        known_devices = [
            f"dev-{index:06d}-{self.rng.randint(1000, 9999)}",
            f"mob-{index:06d}-{self.rng.randint(1000, 9999)}",
        ]
        usual_countries = [country]
        if behavior in {"travel_heavy", "business_owner"}:
            usual_countries.append(self.rng.choice([c for c in COUNTRY_CITIES if c != country]))
        return {
            "customer_id": f"CUST-{index:07d}",
            "full_name": f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(LAST_NAMES)}",
            "age": self.rng.randint(18, 82),
            "country": country,
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "account_age_days": self._account_age(risk_profile),
            "average_spending": round(avg_spend, 2),
            "risk_profile": risk_profile,
            "behavior_pattern": behavior,
            "known_devices": known_devices,
            "usual_countries": usual_countries,
            "fraud_history_count": self._fraud_history(risk_profile),
        }

    def generate_many(self, count: int = 5000) -> list[dict[str, Any]]:
        return [self.generate_customer(i) for i in range(1, count + 1)]

    def _behavior_for_profile(self, risk_profile: str) -> str:
        if risk_profile == "FRAUDSTER":
            return "fraudster_profile"
        if risk_profile == "VIP":
            return self.rng.choice(["travel_heavy", "business_owner"])
        if risk_profile == "HIGH":
            return self.rng.choice(["digital_native", "travel_heavy", "business_owner"])
        return self.rng.choice([p for p in BEHAVIOR_PATTERNS if p != "fraudster_profile"])

    def _average_spend(self, risk_profile: str) -> float:
        if risk_profile == "VIP":
            return self.rng.uniform(350, 1800)
        if risk_profile == "HIGH":
            return self.rng.uniform(90, 650)
        if risk_profile == "FRAUDSTER":
            return self.rng.uniform(80, 350)
        if risk_profile == "MEDIUM":
            return self.rng.uniform(45, 280)
        return self.rng.uniform(15, 160)

    def _account_age(self, risk_profile: str) -> int:
        if risk_profile == "FRAUDSTER":
            return self.rng.randint(3, 180)
        if risk_profile == "HIGH":
            return self.rng.randint(15, 1200)
        if risk_profile == "VIP":
            return self.rng.randint(900, 4200)
        return self.rng.randint(60, 3600)

    def _fraud_history(self, risk_profile: str) -> int:
        if risk_profile == "FRAUDSTER":
            return self.rng.randint(1, 5)
        if risk_profile == "HIGH":
            return self.rng.choices([0, 1, 2], weights=[60, 30, 10], k=1)[0]
        if risk_profile == "MEDIUM":
            return self.rng.choices([0, 1], weights=[92, 8], k=1)[0]
        return 0

