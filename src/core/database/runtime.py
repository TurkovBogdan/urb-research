"""Database runtime: declarative base, engine/session, lifecycle.

Один процесс — один engine. Фабрика сессий и engine лежат на уровне модуля,
``init_database`` создаёт их, ``close_database`` сбрасывает.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import Config


# ── Declarative base ─────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Корневая SQLAlchemy declarative base для всех ORM-моделей."""

    def to_row(self, skip: frozenset[str] = frozenset()) -> dict:
        """Сериализовать в dict по колонкам таблицы. Используется в upsert."""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
            if c.name not in skip
        }


# ── Module-level engine/factory ──────────────────────────────────────────────

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_database(config: Config) -> AsyncEngine:
    """Создать engine + session-factory. Идемпотентно для повторного вызова."""
    # Импорт моделей запускает их регистрацию в ``Base.metadata``.
    # Делается лениво, чтобы избежать циркулярного импорта на старте модуля.
    import src.core.models  # noqa: F401

    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = create_async_engine(
        config.database_url,
        echo=config.db_echo,
        future=True,
        **config.engine_kwargs,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    return _engine


async def close_database() -> None:
    """Закрыть engine и сбросить фабрику."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine() -> AsyncEngine | None:
    """Текущий engine или None, если ``init_database`` не вызывался."""
    return _engine


async def create_all(engine: AsyncEngine) -> None:
    """Создать все таблицы из ОРМ-моделей (только in-memory SQLite тестов; файловые БД — Alembic).

    Полагается на наполненный ``Base.metadata`` — модули, у которых есть таблицы,
    должны быть импортированы к этому моменту (как и ``init_database`` тянет
    ``src.core.models``).
    """
    import src.core.models  # noqa: F401  (регистрация моделей ядра в Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── Session access ───────────────────────────────────────────────────────────

@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Транзакционный контекст вне HTTP-запроса (фоновые задачи, скрипты)."""
    assert _session_factory is not None, "init_database() not called"
    session = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


__all__ = [
    "Base",
    "close_database",
    "get_engine",
    "init_database",
    "session_scope",
]
