"""Фикстуры core_interface: база с таблицей настроек и HTTP-клиент над зон-роутером."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.api import register_exception_handlers
from src.core.config import Config
from src.core.database import close_database, init_database
from src.core.database.runtime import Base
from src.modules.core_interface.api import internal_router


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    import src.modules.core_interface.models  # noqa: F401 — register tables

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_database()


@pytest.fixture
async def client(db):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(internal_router, prefix="/internal/core/interface")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
