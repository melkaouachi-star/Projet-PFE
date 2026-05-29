"""Synthetic transaction and fraud-scenario generator."""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.simulation.catalogs import (
    BEHAVIOR_PATTERNS,
    BROWSERS,
    CARD_TYPES,
    COUNTRY_CITIES,
    CURRENCY_BY_COUNTRY,
    MERCHANTS,
    OPERATING_SYSTEMS,
    PAYMENT_METHODS,
    SCENARIOS,
)
from src.simulation.customers import CustomerGenerator


@dataclass
class TransactionGenerator:
    seed: int = 42
    customers: list[dict[str, Any]] | None = None
    _last_timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        if not self.customers:
            self.customers = CustomerGenerator(seed=self.seed).generate_many(1000)

    def generate_transaction(
        self,
        rate_tps: int = 10,
        fraud_ratio: float = 0.08,
        scenario: str | None = None,
    ) -> dict[str, Any]:
        customer = self.rng.choice(self.customers or [])
        scenario = scenario or self._choose_scenario(customer, fraud_ratio)
        timestamp = self._next_timestamp(rate_tps, scenario)
        return self._build_transaction(customer, timestamp, scenario)

    def generate_batch(self, count: int, rate_tps: int, fraud_ratio: float) -> list[dict[str, Any]]:
        return [
            self.generate_transaction(rate_tps=rate_tps, fraud_ratio=fraud_ratio)
            for _ in range(count)
        ]

    def _choose_scenario(self, customer: dict[str, Any], fraud_ratio: float) -> str:
        if customer["risk_profile"] == "FRAUDSTER" and self.rng.random() < 0.55:
            return self.rng.choice(SCENARIOS)
        if self.rng.random() < fraud_ratio:
            return self.rng.choice(SCENARIOS)
        if self.rng.random() < 0.04:
            return self.rng.choice(["high_amount", "night_transaction", "foreign_country"])
        return "normal"

    def _next_timestamp(self, rate_tps: int, scenario: str) -> datetime:
        rate_tps = max(1, rate_tps)
        if scenario == "night_transaction":
            base = datetime.utcnow().replace(hour=self.rng.choice([0, 1, 2, 3, 23]), minute=self.rng.randint(0, 59))
            self._last_timestamp = base
            return base
        self._last_timestamp = self._last_timestamp + timedelta(seconds=1 / rate_tps)
        return self._last_timestamp

    def _build_transaction(self, customer: dict[str, Any], timestamp: datetime, scenario: str) -> dict[str, Any]:
        country, city, lat, lon = self._location(customer, scenario)
        merchant_category = self._merchant_category(customer, scenario)
        merchant_name = self.rng.choice(MERCHANTS[merchant_category])
        amount = self._amount(customer, scenario, merchant_category)
        known_device = scenario not in {"stolen_card_behavior", "account_takeover", "bot_generated_fraud"}
        device_id = self.rng.choice(customer["known_devices"]) if known_device else self._device_id("unknown")
        ip_reputation, ip_risk, is_vpn, is_tor = self._ip_intelligence(scenario)

        browser = self.rng.choice(BROWSERS)
        os_name = self.rng.choice(OPERATING_SYSTEMS)
        if scenario == "bot_generated_fraud":
            browser = self.rng.choice(["Headless Chrome", "Python Requests", "Selenium"])
            os_name = self.rng.choice(["Linux", "Unknown"])

        return {
            "transaction_id": f"TX-{timestamp:%Y%m%d%H%M%S}-{uuid.uuid4().hex[:10].upper()}",
            "customer_id": customer["customer_id"],
            "customer_name": customer["full_name"],
            "customer_age": customer["age"],
            "customer_risk_category": customer["risk_profile"],
            "customer_home_country": customer["country"],
            "customer_home_city": customer["city"],
            "customer_home_latitude": customer["latitude"],
            "customer_home_longitude": customer["longitude"],
            "account_age_days": customer["account_age_days"],
            "customer_average_spending": customer["average_spending"],
            "fraud_history_count": customer["fraud_history_count"],
            "transaction_amount": amount,
            "transaction_currency": CURRENCY_BY_COUNTRY.get(country, "USD"),
            "merchant_name": merchant_name,
            "merchant_category": merchant_category,
            "transaction_date": timestamp.strftime("%Y-%m-%d"),
            "transaction_time": timestamp.strftime("%H:%M:%S"),
            "timestamp": timestamp.isoformat(),
            "country": country,
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "ip_address": self._ip_address(scenario),
            "ip_reputation": ip_reputation,
            "ip_risk_score": ip_risk,
            "is_vpn": is_vpn,
            "is_tor": is_tor,
            "device_id": device_id,
            "known_device": known_device,
            "browser": browser,
            "operating_system": os_name,
            "payment_method": self._payment_method(scenario),
            "card_type": self._card_type(scenario),
            "transaction_status": "PENDING",
            "recent_transactions_60s": self._recent_count_hint(scenario),
            "scenario": scenario,
        }

    def _location(self, customer: dict[str, Any], scenario: str) -> tuple[str, str, float, float]:
        if scenario in {"foreign_country", "impossible_travel", "stolen_card_behavior", "account_takeover"}:
            countries = [c for c in COUNTRY_CITIES if c != customer["country"]]
            country = self.rng.choice(countries)
        else:
            country = self.rng.choice(customer.get("usual_countries") or [customer["country"]])
        city, lat, lon = self.rng.choice(COUNTRY_CITIES[country])
        return country, city, lat, lon

    def _merchant_category(self, customer: dict[str, Any], scenario: str) -> str:
        if scenario in {"stolen_card_behavior", "bot_generated_fraud", "account_takeover"}:
            return self.rng.choice(["Gift Cards", "Crypto Exchange", "Luxury Goods", "Electronics"])
        if scenario == "anomalous_spending_pattern":
            return self.rng.choice(["Luxury Goods", "Travel", "Crypto Exchange"])
        pattern = customer.get("behavior_pattern", "daily_retail")
        categories = BEHAVIOR_PATTERNS.get(pattern, BEHAVIOR_PATTERNS["daily_retail"])
        return self.rng.choice(categories)

    def _amount(self, customer: dict[str, Any], scenario: str, merchant_category: str) -> float:
        avg = customer["average_spending"]
        multiplier = {
            "normal": self.rng.uniform(0.2, 1.8),
            "high_amount": self.rng.uniform(8, 22),
            "night_transaction": self.rng.uniform(1, 5),
            "foreign_country": self.rng.uniform(1.5, 7),
            "impossible_travel": self.rng.uniform(2, 10),
            "rapid_transaction_burst": self.rng.uniform(0.5, 3),
            "stolen_card_behavior": self.rng.uniform(5, 18),
            "bot_generated_fraud": self.rng.uniform(1, 9),
            "multiple_transactions_different_ips": self.rng.uniform(1, 7),
            "account_takeover": self.rng.uniform(7, 24),
            "anomalous_spending_pattern": self.rng.uniform(6, 18),
        }.get(scenario, 1.0)
        category_boost = 1.4 if merchant_category in {"Luxury Goods", "Travel", "Crypto Exchange"} else 1.0
        amount = max(1.0, avg * multiplier * category_boost)
        return round(min(amount, self.rng.uniform(12000, 45000)), 2)

    def _ip_address(self, scenario: str) -> str:
        if scenario in {"bot_generated_fraud", "stolen_card_behavior", "account_takeover"}:
            prefix = self.rng.choice(["203.0.113", "198.51.100"])
        else:
            prefix = self.rng.choice(["192.0.2", "198.51.100", "203.0.113"])
        return f"{prefix}.{self.rng.randint(1, 254)}"

    def _ip_intelligence(self, scenario: str) -> tuple[str, int, bool, bool]:
        if scenario == "bot_generated_fraud":
            return "botnet", 32, True, False
        if scenario == "stolen_card_behavior":
            return self.rng.choice(["proxy", "blacklisted"]), self.rng.randint(18, 35), True, False
        if scenario == "account_takeover":
            return self.rng.choice(["vpn", "tor", "blacklisted"]), self.rng.randint(16, 35), True, self.rng.random() < 0.25
        if scenario == "multiple_transactions_different_ips":
            return "proxy", 18, True, False
        if self.rng.random() < 0.08:
            return "new", 5, False, False
        return "clean", 0, False, False

    def _device_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:16]}"

    def _payment_method(self, scenario: str) -> str:
        if scenario in {"bot_generated_fraud", "stolen_card_behavior"}:
            return self.rng.choice(["Virtual Card", "Credit Card"])
        return self.rng.choice(PAYMENT_METHODS)

    def _card_type(self, scenario: str) -> str:
        if scenario in {"bot_generated_fraud", "account_takeover"}:
            return self.rng.choice(["Prepaid", "Virtual"])
        return self.rng.choice(CARD_TYPES)

    def _recent_count_hint(self, scenario: str) -> int:
        if scenario == "rapid_transaction_burst":
            return self.rng.randint(8, 25)
        if scenario == "multiple_transactions_different_ips":
            return self.rng.randint(3, 12)
        if scenario == "bot_generated_fraud":
            return self.rng.randint(6, 18)
        return self.rng.randint(0, 2)

