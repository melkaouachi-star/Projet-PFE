"""Background simulation service for live banking transaction streams."""
from __future__ import annotations

import asyncio
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database import crud  # noqa: E402
from src.database.session import SessionLocal  # noqa: E402
from src.scoring.dynamic_engine import MODEL_VERSION, DynamicFraudScoringEngine, assessment_to_event  # noqa: E402
from src.simulation.transactions import TransactionGenerator  # noqa: E402
from src.streaming.broker import EventBroker, get_broker  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger("streaming.simulator")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SimulatorState:
    running: bool = False
    rate_tps: int = 10
    fraud_ratio: float = 0.08
    generated: int = 0
    started_at: str | None = None
    last_error: str | None = None
    run_id: str | None = None


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
        self._task: asyncio.Task[None] | None = None

    async def start(self, rate_tps: int = 10, fraud_ratio: float = 0.08) -> dict[str, Any]:
        self.state.rate_tps = _clamp_rate(rate_tps)
        self.state.fraud_ratio = max(0.0, min(1.0, fraud_ratio))
        self.state.last_error = None
        if self._task and not self._task.done():
            self.state.running = True
            return self.status()
        self.state.running = True
        self.state.started_at = _utc_now().isoformat()
        self.state.generated = 0
        # Open a SimulationRun row so Power BI can slice by discrete run.
        # Guarded: a DB hiccup here must never prevent the simulator starting.
        self.state.run_id = f"RUN-{_utc_now():%Y%m%d%H%M%S}-{uuid.uuid4().hex[:6].upper()}"
        try:
            with SessionLocal() as db:
                crud.create_simulation_run(
                    db,
                    run_id=self.state.run_id,
                    rate_tps=self.state.rate_tps,
                    fraud_ratio=self.state.fraud_ratio,
                    model_version=MODEL_VERSION,
                )
        except Exception as exc:  # pragma: no cover - defensive
            self.state.last_error = f"run-open failed: {exc}"
            log.warning(f"Could not open simulation run row: {exc}")
        self._task = asyncio.create_task(self._run(), name="fraud-simulation-service")
        log.info(
            f"Started simulation {self.state.run_id} at {self.state.rate_tps} TPS, "
            f"fraud_ratio={self.state.fraud_ratio:.2f}"
        )
        return self.status()

    async def stop(self) -> dict[str, Any]:
        self.state.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # Close out the run and snapshot its effectiveness metrics.
        if self.state.run_id:
            try:
                with SessionLocal() as db:
                    crud.finalize_simulation_run(db, self.state.run_id)
            except Exception as exc:  # pragma: no cover - defensive
                self.state.last_error = f"run-close failed: {exc}"
                log.warning(f"Could not finalize simulation run row: {exc}")
        log.info(f"Stopped simulation {self.state.run_id}.")
        return self.status()

    def configure_customers(self, customers: list[dict[str, Any]]) -> None:
        if customers:
            self.generator.customers = customers

    def status(self) -> dict[str, Any]:
        return {
            "running": self.state.running,
            "rate_tps": self.state.rate_tps,
            "fraud_ratio": self.state.fraud_ratio,
            "generated": self.state.generated,
            "started_at": self.state.started_at,
            "last_error": self.state.last_error,
            "run_id": self.state.run_id,
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
                        crud.record_banking_assessment(
                            db, transaction, assessment_payload,
                            simulation_run_id=self.state.run_id,
                        )
                    event = assessment_to_event(transaction, assessment)
                    event["simulation_run_id"] = self.state.run_id
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

