"""Background simulation service for live banking transaction streams."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from src.database import crud
from src.database.session import SessionLocal
from src.scoring.dynamic_engine import DynamicFraudScoringEngine, assessment_to_event
from src.simulation.transactions import TransactionGenerator
from src.streaming.broker import EventBroker, get_broker
from src.utils.logger import get_logger

log = get_logger("streaming.simulator")


@dataclass
class SimulatorState:
    running: bool = False
    rate_tps: int = 10
    fraud_ratio: float = 0.08
    generated: int = 0
    started_at: str | None = None
    last_error: str | None = None


class SimulationService:
    def __init__(
        self,
        broker: EventBroker | None = None,
        engine: DynamicFraudScoringEngine | None = None,
        generator: TransactionGenerator | None = None,
    ):
        self.broker = broker or get_broker()
        self.engine = engine or DynamicFraudScoringEngine()
        self.generator = generator or TransactionGenerator()
        self.state = SimulatorState()
        self._task: asyncio.Task | None = None

    async def start(self, rate_tps: int = 10, fraud_ratio: float = 0.08) -> dict:
        self.state.rate_tps = _clamp_rate(rate_tps)
        self.state.fraud_ratio = max(0.0, min(1.0, fraud_ratio))
        self.state.last_error = None
        if self._task and not self._task.done():
            self.state.running = True
            return self.status()
        self.state.running = True
        self.state.started_at = datetime.utcnow().isoformat()
        self._task = asyncio.create_task(self._run(), name="fraud-simulation-service")
        log.info(f"Started simulation at {self.state.rate_tps} TPS, fraud_ratio={self.state.fraud_ratio:.2f}")
        return self.status()

    async def stop(self) -> dict:
        self.state.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("Stopped simulation.")
        return self.status()

    def configure_customers(self, customers: list[dict]) -> None:
        if customers:
            self.generator.customers = customers

    def status(self) -> dict:
        return {
            "running": self.state.running,
            "rate_tps": self.state.rate_tps,
            "fraud_ratio": self.state.fraud_ratio,
            "generated": self.state.generated,
            "started_at": self.state.started_at,
            "last_error": self.state.last_error,
        }

    async def _run(self) -> None:
        while self.state.running:
            batch_size = self._batch_size()
            interval = batch_size / max(1, self.state.rate_tps)
            try:
                transactions = self.generator.generate_batch(
                    count=batch_size,
                    rate_tps=self.state.rate_tps,
                    fraud_ratio=self.state.fraud_ratio,
                )
                for transaction in transactions:
                    assessment = self.engine.score(transaction)
                    assessment_payload = assessment.as_dict()
                    with SessionLocal() as db:
                        crud.record_banking_assessment(db, transaction, assessment_payload)
                    event = assessment_to_event(transaction, assessment)
                    await self.broker.publish(event)
                    self.state.generated += 1
            except Exception as exc:
                self.state.last_error = str(exc)
                log.exception(f"Simulation loop failed: {exc}")
                await asyncio.sleep(1.0)
            await asyncio.sleep(interval)

    def _batch_size(self) -> int:
        if self.state.rate_tps >= 1000:
            return 100
        if self.state.rate_tps >= 100:
            return 25
        return 1


def _clamp_rate(rate_tps: int) -> int:
    if rate_tps <= 10:
        return 10
    if rate_tps <= 100:
        return 100
    return 1000


_SERVICE = SimulationService()


def get_simulation_service() -> SimulationService:
    return _SERVICE

