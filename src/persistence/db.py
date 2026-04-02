"""Database engine and session wiring."""

from __future__ import annotations

from dataclasses import dataclass

from config import DatabaseSettings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool


@dataclass(frozen=True)
class DatabaseManager:
    settings: DatabaseSettings
    engine: Engine
    session_factory: sessionmaker[Session]


def create_database_manager(settings: DatabaseSettings) -> DatabaseManager | None:
    if not settings.enabled or not settings.url:
        return None
    engine_kwargs = {
        "echo": settings.echo,
        "future": True,
    }
    if settings.url.startswith("sqlite"):
        engine_kwargs["poolclass"] = NullPool
    engine = create_engine(settings.url, **engine_kwargs)
    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
        autoflush=False,
    )
    return DatabaseManager(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
    )
