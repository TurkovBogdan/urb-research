"""Стандартные ошибки API (``src.core.api``): конверт + обработчики исключений."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from src.core.api import ApiError, register_exception_handlers

pytestmark = pytest.mark.pure


class _Body(BaseModel):
    n: int


@pytest.fixture
async def client():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/api-error")
    async def _api_error():
        raise ApiError.conflict("email занят", code="email_taken", fields={"email": "занят"})

    @app.get("/http-exc")
    async def _http_exc():
        raise HTTPException(status_code=404, detail="task not registered")

    @app.post("/validate")
    async def _validate(body: _Body):
        return {"n": body.n}

    @app.get("/boom")
    async def _boom():
        raise RuntimeError("kaboom")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_api_error_maps_to_envelope(client):
    r = await client.get("/api-error")
    assert r.status_code == 409
    body = r.json()
    assert body == {"error": "email занят", "code": "email_taken", "fields": {"email": "занят"}}


async def test_http_exception_string_detail_to_error(client):
    r = await client.get("/http-exc")
    assert r.status_code == 404
    assert r.json() == {"error": "task not registered", "code": None, "fields": None}


async def test_validation_error_collects_fields(client):
    r = await client.post("/validate", json={"n": "not-an-int"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "validation_error"
    assert "n" in body["fields"]


async def test_unhandled_exception_is_500(client):
    r = await client.get("/boom")
    assert r.status_code == 500
    assert r.json() == {"error": "Внутренняя ошибка сервера", "code": "internal_error", "fields": None}
