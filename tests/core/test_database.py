"""Database runtime: init/close, session_scope."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config import Config
from src.core.database import (
    close_database,
    get_engine,
    init_database,
    session_scope,
)



@pytest.fixture
def config() -> Config:
    return Config()


@pytest.fixture
async def db(config: Config):
    await init_database(config)
    try:
        yield
    finally:
        await close_database()


@pytest.mark.db
async def test_init_database_sets_engine(db):
    assert isinstance(get_engine(), AsyncEngine)


@pytest.mark.db
async def test_close_database_clears_engine(config: Config):
    await init_database(config)
    await close_database()
    assert get_engine() is None


@pytest.mark.db
async def test_engine_real_connection(db):
    engine = get_engine()
    assert engine is not None
    async with engine.connect() as conn:
        result = await conn.execute(text("select 1"))
        assert result.scalar() == 1


@pytest.mark.db
async def test_session_scope_commits(db):
    async with session_scope() as session:
        result = await session.execute(text("select 42"))
        assert result.scalar() == 42


@pytest.mark.db
async def test_session_scope_rollback_on_error(db):
    with pytest.raises(RuntimeError):
        async with session_scope() as session:
            await session.execute(text("select 1"))
            raise RuntimeError("boom")
