"""
SQLAlchemy engine & session factory.

`get_session()` is intended to be used as a FastAPI dependency
(`Depends(get_session)`).  It transparently supports SQLite (default
for local dev) or PostgreSQL (production) via the `DATABASE_URL`
environment variable.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.utils.config import get_config

_cfg = get_config().database
DATABASE_URL = os.getenv("DATABASE_URL", _cfg.url)
# Render Postgres exposes URLs as `postgres://...` but SQLAlchemy 2.x
# only accepts the explicit driver form.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=_cfg.echo, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def init_db() -> None:
    """Create tables - safe to call multiple times."""
    from src.database import models  # noqa: F401 (register models)
    Base.metadata.create_all(bind=engine)
    _ensure_banking_schema_compat()


def _ensure_banking_schema_compat() -> None:
    """Add missing columns for existing demo databases.

    SQLAlchemy's ``create_all`` creates missing tables but does not migrate
    existing ones. The banking platform evolved during development, so local
    SQLite/PostgreSQL databases may still contain older versions of the live
    simulation tables. This lightweight additive migration keeps demos working
    without dropping data. Production deployments should still use Alembic.
    """
    target_tables = {
        "banking_customers",
        "banking_transactions",
        "banking_alerts",
        "banking_shap_explanations",
    }
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    quote = engine.dialect.identifier_preparer.quote

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in target_tables or table.name not in existing_tables:
                continue
            existing_cols = {col["name"] for col in inspector.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing_cols:
                    continue
                col_type = col.type.compile(dialect=engine.dialect)
                ddl = f"ALTER TABLE {quote(table.name)} ADD COLUMN {quote(col.name)} {col_type}"
                conn.execute(text(ddl))


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a managed SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context-manager variant for scripts."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
