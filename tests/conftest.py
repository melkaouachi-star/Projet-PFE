"""
Shared pytest configuration.

Forces every test process to use a single in-memory SQLite database that is
*shared across threads*.  Without this, FastAPI sync endpoints (which run in
Starlette's threadpool) receive a fresh, empty SQLite connection because
``sqlite:///:memory:`` is connection-scoped by default.

Set BEFORE any ``src.*`` module is imported so ``src.database.session``
picks up the override when the engine is constructed.
"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///file:fraud_test_db?mode=memory&cache=shared&uri=true")

# Patch the engine to use StaticPool so every connection (including threadpool
# workers) maps to the *same* SQLite in-memory database.  We do this once at
# import time so module-level fixtures in test files see a consistent engine.
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from src.database import session as _session  # noqa: E402

_shared_engine = create_engine(
    os.environ["DATABASE_URL"],
    echo=False,
    connect_args={"check_same_thread": False, "uri": True},
    poolclass=StaticPool,
    future=True,
)

_session.engine = _shared_engine
_session.SessionLocal.configure(bind=_shared_engine)

# Make sure tables exist for any test that doesn't manage them itself.
from src.database import models  # noqa: E402, F401
_session.Base.metadata.create_all(bind=_shared_engine)
