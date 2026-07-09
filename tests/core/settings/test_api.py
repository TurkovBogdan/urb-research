"""HTTP API подсистемы settings."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.settings.api import router as settings_router
from src.core.settings.bootstrap import (
    load_initial_stores,
    register_settings_schemas,
)
from src.core.api import register_exception_handlers
from src.core.settings.fields import ChoiceField, IntField, StrField
from src.core.config import Config
from src.core.database import close_database, init_database
from src.core.database.runtime import Base

from src.core.module import Module


class _M(Module):
    name = "api_m"
    settings_schema = (
        IntField(key="n", label="N", default_=5, min=0, max=100),
        ChoiceField(
            key="mode", label="Mode", default_="a",
            options={"a": "A", "b": "B"},
        ),
    )


class _SecretM(Module):
    name = "secret_m"
    settings_schema = (
        StrField(key="token", label="Token", secret=True),
    )


@pytest.fixture
async def app():
    engine = await init_database(Config())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    modules = [_M(), _SecretM()]
    register_settings_schemas(modules)
    await load_initial_stores(modules)
    fastapi_app = FastAPI()
    register_exception_handlers(fastapi_app)
    fastapi_app.include_router(settings_router, prefix="/internal/core/settings")
    try:
        yield fastapi_app
    finally:
        await close_database()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.db
async def test_list_modules(client):
    r = await client.get("/internal/core/settings/modules")
    assert r.status_code == 200
    data = r.json()
    assert any(m["module"] == "api_m" for m in data)


@pytest.mark.db
async def test_get_module(client):
    r = await client.get("/internal/core/settings/api_m")
    assert r.status_code == 200
    body = r.json()
    assert body["values"] == {"n": 5, "mode": "a"}
    keys = [f["key"] for f in body["fields"]]
    assert keys == ["n", "mode"]


@pytest.mark.db
async def test_put_valid_value(client):
    r = await client.put(
        "/internal/core/settings/api_m/n", json={"value": 42}
    )
    assert r.status_code == 200
    assert r.json()["values"]["n"] == 42


@pytest.mark.db
async def test_put_invalid_value_returns_422(client):
    r = await client.put(
        "/internal/core/settings/api_m/n", json={"value": 999}
    )
    assert r.status_code == 422
    body = r.json()
    assert body["fields"]["n"]
    assert body["error"]


@pytest.mark.db
async def test_put_unknown_key_returns_404(client):
    r = await client.put(
        "/internal/core/settings/api_m/no_such_key", json={"value": 1}
    )
    assert r.status_code == 404


@pytest.mark.db
async def test_post_reset(client):
    await client.put("/internal/core/settings/api_m/n", json={"value": 42})
    r = await client.post("/internal/core/settings/api_m/n/reset")
    assert r.status_code == 200
    assert r.json()["values"]["n"] == 5


@pytest.mark.db
async def test_post_reset_unknown_key_returns_404(client):
    r = await client.post("/internal/core/settings/api_m/nope/reset")
    assert r.status_code == 404


@pytest.mark.db
async def test_get_unknown_module_returns_404(client):
    r = await client.get("/internal/core/settings/no_such_module")
    assert r.status_code == 404


def _token_field(body: dict) -> dict:
    return next(f for f in body["fields"] if f["key"] == "token")


def _stored_token() -> str:
    """Реальное значение секрета в store (не маскированное API-представление)."""
    from src.core.settings.registry import get_registry

    return get_registry().get("secret_m").token


async def _set_token(client, value: str):
    return await client.put(
        "/internal/core/settings/secret_m/token", json={"value": value}
    )


@pytest.mark.db
async def test_secret_unset_masked_and_is_set_false(client):
    body = (await client.get("/internal/core/settings/secret_m")).json()
    assert body["values"]["token"] == ""
    assert _token_field(body)["is_set"] is False
    assert _stored_token() == ""


@pytest.mark.db
async def test_secret_set_stores_value_but_returns_sentinel(client):
    await _set_token(client, "s3cr3t")
    assert _stored_token() == "s3cr3t"              # реально сохранён
    body = (await client.get("/internal/core/settings/secret_m")).json()
    assert body["values"]["token"] == "NOT_CHANGED"  # наружу — сентинел, не токен
    assert "s3cr3t" not in str(body)
    assert _token_field(body)["is_set"] is True


@pytest.mark.db
async def test_secret_update_replaces_value(client):
    await _set_token(client, "old-token")
    await _set_token(client, "new-token")
    assert _stored_token() == "new-token"           # новое значение перезаписало старое


@pytest.mark.db
async def test_sentinel_put_does_not_overwrite_token(client):
    await _set_token(client, "keepme")
    # Пользователь не трогал поле → форма прислала обратно сам сентинел.
    r = await _set_token(client, "NOT_CHANGED")
    assert r.status_code == 200
    # Токен не заменён на литерал "NOT_CHANGED" и не очищен — остался прежним.
    assert _stored_token() == "keepme"


@pytest.mark.db
async def test_blank_put_does_not_overwrite_token(client):
    await _set_token(client, "keepme")
    r = await _set_token(client, "")
    assert r.status_code == 200
    assert _stored_token() == "keepme"


@pytest.mark.db
async def test_reset_clears_secret(client):
    await _set_token(client, "keepme")
    r = await client.post("/internal/core/settings/secret_m/token/reset")
    assert r.status_code == 200
    assert _stored_token() == ""                     # очистка — только через reset
