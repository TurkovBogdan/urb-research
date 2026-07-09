"""Реестр guard'ов + метка ``@guard`` + зон-guard (``src.core.router``)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient

from src.core.api import ApiError, register_exception_handlers
from src.core.router import (
    GuardRegistry,
    guard,
    guard_allow_all,
    guard_deny_all,
    guard_rules,
    is_allow_all,
    is_deny_all,
    make_zone_guard,
)

pytestmark = pytest.mark.pure


# Локальные test-double'ы вместо снятых core-моков (auth/ability теперь даёт core_users).
# Ядро принципала не типизирует (duck-typed request.state.user) — достаточно объекта нужной формы.
_STUB_USER = SimpleNamespace(
    id=1, email="admin@semaphore.local", group="admin", is_active=True
)


async def mock_auth_guard(request: Request) -> None:
    request.state.user = _STUB_USER


async def mock_ability_guard(request: Request) -> None:
    return


# ── реестр ───────────────────────────────────────────────────────────────────
def test_registry_add_resolve_has():
    reg = GuardRegistry()
    reg.add("allow_all", guard_allow_all)
    assert reg.has("allow_all")
    assert reg.resolve("allow_all") is guard_allow_all
    assert not reg.has("nope")


def test_registry_duplicate_raises():
    reg = GuardRegistry()
    reg.add("auth", mock_auth_guard)
    with pytest.raises(ValueError):
        reg.add("auth", mock_auth_guard)


# ── метка @guard ─────────────────────────────────────────────────────────────
def test_guard_decorator_accumulates_rules():
    @guard("ability", "admin:read")
    @guard("ability", "users:write")
    async def ep(): ...

    assert guard_rules(ep) == (("ability", "users:write"), ("ability", "admin:read"))


def test_is_allow_all_is_deny_all():
    @guard("allow_all")
    async def pub(): ...

    @guard("deny_all")
    async def dis(): ...

    async def plain(): ...

    assert is_allow_all(pub) and not is_deny_all(pub)
    assert is_deny_all(dis) and not is_allow_all(dis)
    assert not is_allow_all(plain) and not is_deny_all(plain)


# ── зон-guard через приложение ───────────────────────────────────────────────
def _registry(extra: dict | None = None) -> GuardRegistry:
    reg = GuardRegistry()
    reg.add("allow_all", guard_allow_all)
    reg.add("deny_all", guard_deny_all)
    reg.add("auth", mock_auth_guard)
    reg.add("ability", mock_ability_guard)
    for kind, g in (extra or {}).items():
        reg.add(kind, g)
    return reg


def _app(default: list[str], routes, extra: dict | None = None) -> FastAPI:
    router = APIRouter()
    routes(router)
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(
        router, dependencies=[Depends(make_zone_guard(_registry(extra), default))]
    )
    return app


async def _get(app: FastAPI, path: str):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        return await c.get(path)


async def test_default_auth_allows_and_sets_user():
    def routes(r):
        @r.get("/x")
        async def x(request: Request):
            return {"user": request.state.user.email}

    res = await _get(_app(["auth"], routes), "/x")
    assert res.status_code == 200
    assert res.json() == {"user": "admin@semaphore.local"}


async def test_allow_all_bypasses_default():
    def routes(r):
        @r.get("/closed")
        async def closed():
            return {"ok": True}

        @r.get("/open")
        @guard("allow_all")
        async def open_():
            return {"ok": True}

    app = _app(["deny_all"], routes)  # зона закрыта по умолчанию
    assert (await _get(app, "/closed")).status_code == 401
    assert (await _get(app, "/open")).status_code == 200


async def test_deny_all_label_blocks_even_with_auth_default():
    def routes(r):
        @r.get("/off")
        @guard("deny_all")
        async def off():
            return {"ok": True}

    assert (await _get(_app(["auth"], routes), "/off")).status_code == 401


async def test_empty_default_no_marks_falls_back_to_deny_all():
    def routes(r):
        @r.get("/x")
        async def x():
            return {"ok": True}

    assert (await _get(_app([], routes), "/x")).status_code == 401


async def test_ability_mock_passes():
    def routes(r):
        @r.get("/x")
        @guard("ability", "admin:read")
        async def x():
            return {"ok": True}

    assert (await _get(_app(["auth"], routes), "/x")).status_code == 200


async def test_guards_run_in_order_first_raise_stops():
    calls: list[str] = []

    async def g_ok(request):
        calls.append("ok")

    async def g_boom(request):
        calls.append("boom")
        raise ApiError.forbidden("stop")

    async def g_after(request):
        calls.append("after")

    def routes(r):
        @r.get("/x")
        @guard("after")
        async def x():
            return {"ok": True}

    extra = {"ok": g_ok, "boom": g_boom, "after": g_after}
    res = await _get(_app(["ok", "boom"], routes, extra), "/x")
    assert res.status_code == 403
    assert calls == ["ok", "boom"]  # "after" не достигнут
