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

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.utils.config import get_config

_cfg = get_config().database
DATABASE_URL = os.getenv("DATABASE_URL", _cfg.url)
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=_cfg.echo, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def init_db() -> None:
    """Create tables - safe to call multiple times."""
    from src.database import models  # noqa: F401 (register models)
    Base.metadata.create_all(bind=engine)


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
