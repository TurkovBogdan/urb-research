"""Фикстуры core_connectors: база с таблицей доступов, HTTP-клиент, мастер-ключ."""

from __future__ import annotations

import base64
import os

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.api import register_exception_handlers
from src.core.config import Config
from src.core.database import close_database, init_database
from src.core.database.runtime import Base
from src.modules.core_connectors.api import internal_router


@pytest.fixture
async def db(config: Config):
    engine = await init_database(config)
    import src.modules.core_connectors.access.model  # noqa: F401 — register tables

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
    app.include_router(internal_router, prefix="/internal")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _no_env_seeds(monkeypatch):
    """Убрать из окружения ключи, которые разовый импорт умеет подхватывать.

    Иначе тест зависел бы от оболочки разработчика: `TAVILY_API_KEY`, выставленный для
    другой утилиты, молча превращался бы в запись доступа посреди прогона.
    """
    from src.modules.core_connectors.connectors import BUILTIN_CONNECTORS

    for connector in BUILTIN_CONNECTORS:
        for field in connector.FIELDS:
            monkeypatch.delenv(f"{connector.SERVICE}_{field.key}".upper(), raising=False)


@pytest.fixture(autouse=True)
def _no_master_key(monkeypatch):
    """По умолчанию прогон идёт без шифрования — независимо от `.env` разработчика.

    Установка выписывает себе ключ сама при первом старте, и он лежит в том же `.env`,
    который читает `Config` в тестах. Без этой заглушки прогон зависел бы от того,
    запускали ли на машине приложение.
    """
    from src.modules.core_connectors.access import crypto

    monkeypatch.setattr(crypto, "configured_master_key", lambda: "")


@pytest.fixture
def master_key(monkeypatch) -> str:
    """Включить шифрование на время теста."""
    from src.modules.core_connectors.access import crypto

    key = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    monkeypatch.setattr(crypto, "configured_master_key", lambda: key)
    return key
