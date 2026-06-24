"""Database engine, session factory and declarative base (SQLAlchemy 2.0).

Dev uses SQLite (zero install); production sets UE_DATABASE_URL to PostgreSQL.
The same models and migrations run on both.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()
_is_sqlite = _settings.database_url.startswith("sqlite")

engine = create_engine(
    _settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_session() -> Iterator[Session]:
    """FastAPI dependency: a request-scoped DB session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
