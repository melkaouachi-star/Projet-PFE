"""Dynamic fraud scoring for realistic banking transactions.

The engine combines customer profile risk, behavioral drift, transaction
velocity, geo/IP/device signals and fraud-scenario hints into a calibrated
0-100 probability and a 0-100 risk score.  It intentionally keeps the scoring
logic inspectable so it can double as a SHAP-style local explanation layer in
demo and thesis settings.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from math import asin, cos, exp, radians, sin, sqrt
from typing import Any


MODEL_VERSION = "dynamic-fraud-engine-v2.0"


@dataclass
class FeatureContribution:
    feature_name: str
    feature_value: Any
    contribution: float
    shap_value: float
    reason: str


@dataclass
class FraudAssessment:
    fraud_probability: float
    risk_score: int
    fraud_level: str
    decision: str
    threshold: float
    transaction_status: str
    model_version: str
    base_value: float
    top_reasons: list[str]
    contributions: list[FeatureContribution]
    alert_severity: str
    alert_message: str

    def as_dict(self) -> dict[str, Any]:
        feature_names = [c.feature_name for c in self.contributions]
        shap_values = [round(c.shap_value, 4) for c in self.contributions]
        contribution_score = {
            c.feature_name: {
                "value": c.feature_value,
                "risk_points": round(c.contribution, 2),
                "reason": c.reason,
            }
            for c in self.contributions
        }
        return {
            "fraud_probability": round(self.fraud_probability, 2),
            "risk_score": self.risk_score,
            "fraud_level": self.fraud_level,
            "decision": self.decision,
            "threshold": self.threshold,
            "transaction_status": self.transaction_status,
            "model_version": self.model_version,
            "base_value": round(self.base_value, 4),
            "top_reasons": self.top_reasons,
            "feature_names": feature_names,
            "shap_values": shap_values,
            "risk_contribution_score": contribution_score,
            "dynamic_features": contribution_score,
            "alert_severity": self.alert_severity,
            "alert_message": self.alert_message,
        }


class DynamicFraudScoringEngine:
    """Explainable dynamic fraud engine for online banking simulations."""

    PROFILE_BASE_RISK = {
        "LOW": 6,
        "LOW_RISK": 6,
        "MEDIUM": 16,
        "MEDIUM_RISK": 16,
        "HIGH": 32,
        "HIGH_RISK": 32,
        "VIP": 8,
        "FRAUDSTER": 70,
    }
    COUNTRY_RISK = {
        "Russia": 18,
        "Nigeria": 17,
        "Brazil": 9,
        "China": 8,
        "United Arab Emirates": 6,
        "United States": 2,
        "Morocco": 2,
        "France": 2,
        "Germany": 2,
        "United Kingdom": 2,
        "Canada": 2,
        "Spain": 2,
        "Singapore": 1,
    }
    SCENARIO_RISK = {
        "normal": 0,
        "high_amount": 24,
        "night_transaction": 14,
        "foreign_country": 17,
        "impossible_travel": 34,
        "rapid_transaction_burst": 26,
        "stolen_card_behavior": 36,
        "bot_generated_fraud": 32,
        "multiple_transactions_different_ips": 28,
        "account_takeover": 38,
        "anomalous_spending_pattern": 27,
    }
    MERCHANT_RISK = {
        "Crypto Exchange": 14,
        "Gambling": 13,
        "Gift Cards": 12,
        "Luxury Goods": 9,
        "Electronics": 7,
        "Travel": 5,
        "ATM Withdrawal": 8,
    }
    IP_REPUTATION_RISK = {
        "clean": 0,
        "new": 5,
        "vpn": 10,
        "proxy": 14,
        "tor": 22,
        "botnet": 28,
        "blacklisted": 35,
    }

    def __init__(self, block_threshold: float = 70.0, review_threshold: float = 45.0):
        self.block_threshold = block_threshold
        self.review_threshold = review_threshold
        self._customer_history: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=200))

    def score(self, transaction: dict[str, Any]) -> FraudAssessment:
        tx = dict(transaction)
        customer_id = str(tx.get("customer_id", "unknown"))
        timestamp = _coerce_datetime(tx.get("timestamp"))
        tx["timestamp"] = timestamp

        contributions: list[FeatureContribution] = []
        profile = str(tx.get("customer_risk_category", "LOW")).upper().replace(" ", "_")
        base = float(self.PROFILE_BASE_RISK.get(profile, 12))

        self._add(
            contributions,
            "customer_risk_category",
            profile,
            base,
            f"Customer profile baseline risk is {profile.replace('_', ' ').title()}.",
        )

        amount = float(tx.get("transaction_amount", 0.0))
        avg_spend = max(float(tx.get("customer_average_spending", tx.get("average_spending", 120.0))), 1.0)
        amount_ratio = amount / avg_spend
        if amount >= 10000:
            self._add(contributions, "transaction_amount", amount, 28, "Very high absolute transaction amount.")
        elif amount >= 5000:
            self._add(contributions, "transaction_amount", amount, 20, "High absolute transaction amount.")
        elif amount >= 1500:
            self._add(contributions, "transaction_amount", amount, 9, "Moderately high transaction amount.")

        if amount_ratio >= 10:
            self._add(contributions, "amount_vs_customer_average", round(amount_ratio, 2), 30, "Amount is more than 10x the customer's average spend.")
        elif amount_ratio >= 5:
            self._add(contributions, "amount_vs_customer_average", round(amount_ratio, 2), 20, "Amount is more than 5x the customer's average spend.")
        elif amount_ratio >= 2.5:
            self._add(contributions, "amount_vs_customer_average", round(amount_ratio, 2), 10, "Amount is materially above the customer's normal behavior.")

        hour = timestamp.hour
        if hour < 5 or hour >= 23:
            self._add(contributions, "transaction_time", f"{hour:02d}:00", 13, "Transaction occurred during a high-risk night window.")

        country = str(tx.get("country", ""))
        home_country = str(tx.get("customer_home_country", tx.get("home_country", country)))
        if country and home_country and country != home_country:
            self._add(contributions, "foreign_country", country, 15, "Transaction country differs from customer's usual country.")
        country_risk = self.COUNTRY_RISK.get(country, int(tx.get("location_risk_score", 3)))
        if country_risk >= 8:
            self._add(contributions, "geographic_risk", country, country_risk, "Transaction location has elevated fraud-network risk in the simulation.")

        ip_rep = str(tx.get("ip_reputation", "clean")).lower()
        ip_risk = max(self.IP_REPUTATION_RISK.get(ip_rep, 0), int(tx.get("ip_risk_score", 0)))
        if ip_risk >= 8:
            self._add(contributions, "ip_reputation", ip_rep, ip_risk, "IP intelligence indicates anonymization, automation, or abuse history.")
        if bool(tx.get("is_tor", False)):
            self._add(contributions, "tor_exit_node", True, 16, "Transaction originated from a Tor exit node.")
        elif bool(tx.get("is_vpn", False)):
            self._add(contributions, "vpn_or_proxy", True, 8, "Transaction used a VPN or proxy network.")

        if not bool(tx.get("known_device", False)):
            self._add(contributions, "device_id", tx.get("device_id"), 12, "Device is not known for this customer.")

        merchant_category = str(tx.get("merchant_category", "Retail"))
        merchant_risk = self.MERCHANT_RISK.get(merchant_category, 0)
        if merchant_risk:
            self._add(contributions, "merchant_category", merchant_category, merchant_risk, "Merchant category is frequently abused in card-not-present fraud.")

        card_type = str(tx.get("card_type", "")).lower()
        if "prepaid" in card_type or "virtual" in card_type:
            self._add(contributions, "card_type", tx.get("card_type"), 7, "Card type has elevated misuse risk in the simulator.")

        account_age = int(tx.get("account_age_days", 365))
        if account_age < 30:
            self._add(contributions, "account_age_days", account_age, 12, "New account with limited behavioral history.")
        elif account_age < 90:
            self._add(contributions, "account_age_days", account_age, 6, "Relatively new account with sparse history.")

        fraud_history = int(tx.get("fraud_history_count", 0))
        if fraud_history:
            self._add(
                contributions,
                "fraud_history_count",
                fraud_history,
                min(25, fraud_history * 8),
                "Customer has previous fraud or chargeback history.",
            )

        recent_count = self._recent_count(customer_id, timestamp)
        recent_count = max(recent_count, int(tx.get("recent_transactions_60s", 0)))
        if recent_count >= 15:
            self._add(contributions, "transaction_frequency_60s", recent_count, 28, "Rapid transaction burst detected within 60 seconds.")
        elif recent_count >= 8:
            self._add(contributions, "transaction_frequency_60s", recent_count, 18, "Elevated transaction velocity within 60 seconds.")
        elif recent_count >= 4:
            self._add(contributions, "transaction_frequency_60s", recent_count, 9, "Customer is transacting more frequently than normal.")

        travel = self._impossible_travel(customer_id, tx)
        if travel is not None:
            distance_km, hours, speed = travel
            self._add(
                contributions,
                "impossible_travel",
                f"{round(distance_km)} km in {round(hours, 2)}h",
                32 if speed > 1200 else 22,
                "Distance and elapsed time imply impossible or highly unlikely travel.",
            )

        ip_churn = self._recent_distinct_ips(customer_id, timestamp)
        if ip_churn >= 4:
            self._add(contributions, "multiple_ip_addresses", ip_churn, 22, "Multiple IP addresses were observed for the same customer in a short window.")
        elif ip_churn >= 2 and tx.get("scenario") == "multiple_transactions_different_ips":
            self._add(contributions, "multiple_ip_addresses", ip_churn, 14, "Customer session is moving across IP addresses.")

        scenario = str(tx.get("scenario", "normal"))
        scenario_points = self.SCENARIO_RISK.get(scenario, 0)
        if scenario_points:
            self._add(
                contributions,
                "fraud_scenario",
                scenario,
                scenario_points,
                f"Simulator injected scenario: {scenario.replace('_', ' ')}.",
            )

        raw_score = sum(c.contribution for c in contributions)
        risk_score = int(round(max(0.0, min(100.0, raw_score))))
        fraud_probability = _sigmoid_probability(risk_score)
        fraud_level, decision, status = self._decision(risk_score)
        ordered = sorted(contributions, key=lambda c: abs(c.contribution), reverse=True)
        top_reasons = [c.reason for c in ordered[:5]]
        severity = "CRITICAL" if risk_score >= 85 else "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 45 else "LOW"
        alert_message = (
            f"{severity} alert: {tx.get('customer_name')} attempted "
            f"{tx.get('transaction_currency', 'USD')} {amount:,.2f} in {tx.get('city')}, "
            f"{tx.get('country')} with risk score {risk_score}."
        )

        self._customer_history[customer_id].append(
            {
                "timestamp": timestamp,
                "latitude": float(tx.get("latitude", 0.0)),
                "longitude": float(tx.get("longitude", 0.0)),
                "ip_address": tx.get("ip_address"),
                "amount": amount,
                "decision": decision,
            }
        )

        return FraudAssessment(
            fraud_probability=fraud_probability,
            risk_score=risk_score,
            fraud_level=fraud_level,
            decision=decision,
            threshold=self.block_threshold,
            transaction_status=status,
            model_version=MODEL_VERSION,
            base_value=base,
            top_reasons=top_reasons or ["Behavior is consistent with customer history."],
            contributions=ordered,
            alert_severity=severity,
            alert_message=alert_message,
        )

    def _recent_count(self, customer_id: str, timestamp: datetime) -> int:
        return sum(
            1
            for event in self._customer_history[customer_id]
            if 0 <= (timestamp - event["timestamp"]).total_seconds() <= 60
        )

    def _recent_distinct_ips(self, customer_id: str, timestamp: datetime) -> int:
        ips = {
            event.get("ip_address")
            for event in self._customer_history[customer_id]
            if 0 <= (timestamp - event["timestamp"]).total_seconds() <= 300
        }
        return len({ip for ip in ips if ip})

    def _impossible_travel(self, customer_id: str, tx: dict[str, Any]) -> tuple[float, float, float] | None:
        history = self._customer_history[customer_id]
        if not history:
            return None
        current_time = _coerce_datetime(tx.get("timestamp"))
        current_lat = float(tx.get("latitude", 0.0))
        current_lon = float(tx.get("longitude", 0.0))
        previous = history[-1]
        delta_seconds = (current_time - previous["timestamp"]).total_seconds()
        if delta_seconds <= 0 or delta_seconds > 12 * 3600:
            return None
        distance = _haversine(previous["latitude"], previous["longitude"], current_lat, current_lon)
        hours = delta_seconds / 3600
        speed = distance / max(hours, 1e-6)
        if distance > 500 and speed > 900:
            return distance, hours, speed
        return None

    @staticmethod
    def _add(
        contributions: list[FeatureContribution],
        feature_name: str,
        value: Any,
        points: float,
        reason: str,
    ) -> None:
        contributions.append(
            FeatureContribution(
                feature_name=feature_name,
                feature_value=value,
                contribution=float(points),
                shap_value=float(points) / 100.0,
                reason=reason,
            )
        )

    def _decision(self, risk_score: int) -> tuple[str, str, str]:
        if risk_score >= 85:
            return "Critical Risk", "BLOCKED", "BLOCKED"
        if risk_score >= self.block_threshold:
            return "High Risk", "BLOCKED", "BLOCKED"
        if risk_score >= self.review_threshold:
            return "Medium Risk", "SUSPICIOUS", "UNDER_REVIEW"
        return "Low Risk", "APPROVED", "APPROVED"


def assessment_to_event(transaction: dict[str, Any], assessment: FraudAssessment) -> dict[str, Any]:
    """Merge the original transaction and score into one dashboard event."""
    payload = dict(transaction)
    if isinstance(payload.get("timestamp"), datetime):
        payload["timestamp"] = payload["timestamp"].isoformat()
    payload.update(assessment.as_dict())
    payload["amount"] = payload.get("transaction_amount")
    payload["currency"] = payload.get("transaction_currency")
    return payload


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    return datetime.utcnow()


def _sigmoid_probability(risk_score: int) -> float:
    probability = 100.0 / (1.0 + exp(-(risk_score - 50) / 11.5))
    if risk_score >= 85:
        probability = max(probability, 92.0 + (risk_score - 85) * 0.45)
    return max(0.0, min(99.8, probability))


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def assessment_dict(transaction: dict[str, Any], assessment: FraudAssessment) -> dict[str, Any]:
    """JSON-friendly detail payload used by REST responses and tests."""
    out = assessment_to_event(transaction, assessment)
    out["contributions"] = [asdict(c) for c in assessment.contributions]
    return out
