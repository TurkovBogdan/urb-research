"""create_app: composition root + lifespan."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.app_factory import create_app
from src.core.config import Config
from src.core.module import Module
from tests.core._support import AuthStubModule


class _StubConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STUB_", extra="ignore")
    value: int = 42


class _StubModule(Module):
    name = "stub"
    config_cls = _StubConfig

    def configure(self, app: FastAPI, config: Config) -> None:
        @app.get("/api/stub/ping")
        async def _ping():
            return {"ok": True}


class _StubModuleNoConfig(Module):
    name = "stub"

    def configure(self, app: FastAPI, config: Config) -> None:
        @app.get("/api/stub/ping")
        async def _ping():
            return {"ok": True}


@pytest.fixture
def config() -> Config:
    return Config()


@pytest.mark.pure
def test_create_app_returns_fastapi(config: Config):
    app = create_app(modules=[AuthStubModule()], config=config)
    assert isinstance(app, FastAPI)


@pytest.mark.pure
def test_create_app_stores_config(config: Config):
    app = create_app(modules=[AuthStubModule()], config=config)
    assert app.state.config is config


@pytest.mark.pure
def test_module_configs_instantiated(config: Config):
    app = create_app(modules=[AuthStubModule(), _StubModule()], config=config)
    assert "stub" in app.state.module_configs
    assert isinstance(app.state.module_configs["stub"], _StubConfig)
    assert app.state.module_configs["stub"].value == 42


@pytest.mark.pure
def test_module_without_config_not_added(config: Config):
    app = create_app(modules=[AuthStubModule(), _StubModuleNoConfig()], config=config)
    assert "stub" not in app.state.module_configs


@pytest.mark.pure
def test_configure_is_called(config: Config):
    app = create_app(modules=[AuthStubModule(), _StubModule()], config=config)
    paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert "/api/stub/ping" in paths


@pytest.mark.pure
def test_server_disabled_skips_core_zone():
    app = create_app(modules=[], config=Config(server_enabled=False))
    paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert not any(p.startswith("/internal/core") for p in paths)


@pytest.mark.pure
def test_server_enabled_mounts_core_zone():
    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    paths = [r.path for r in app.routes if hasattr(r, "path")]
    assert any(p.startswith("/internal/core") for p in paths)


@pytest.mark.pure
async def test_health_public_available_when_api_enabled():
    """Публичный /internal/health доступен без auth при включённом API."""
    from httpx import ASGITransport, AsyncClient

    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/internal/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.pure
async def test_health_absent_when_api_disabled():
    """При выключенном API зоны нет ⇒ /internal/health недоступен (404)."""
    from httpx import ASGITransport, AsyncClient

    app = create_app(modules=[], config=Config(server_enabled=False))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/internal/health")
    assert r.status_code == 404


@pytest.mark.pure
async def test_debug_delay_slows_internal_requests():
    """SERVER_DEBUG_DELAY_MS>0 монтирует зон-задержку — запрос ждёт ≈ заданное время."""
    import time

    from httpx import ASGITransport, AsyncClient

    app = create_app(
        modules=[AuthStubModule()],
        config=Config(server_enabled=True, server_debug_delay_ms=200),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        start = time.perf_counter()
        r = await c.get("/internal/health")
        elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed >= 0.18  # запас от 0.2s на джиттер планировщика


@pytest.mark.pure
async def test_debug_delay_zero_is_fast():
    """SERVER_DEBUG_DELAY_MS=0 (дефолт) — зависимость не монтируется, без задержки."""
    import time

    from httpx import ASGITransport, AsyncClient

    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        start = time.perf_counter()
        r = await c.get("/internal/health")
        elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < 0.1


@pytest.mark.pure
def test_swagger_and_openapi_disabled():
    """Swagger/OpenAPI выключены в обоих режимах — внутренний API, схему не публикуем."""
    for enabled in (True, False):
        app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=enabled))
        assert app.docs_url is None
        assert app.openapi_url is None
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert not any(p in ("/docs", "/openapi.json") for p in paths)


class _BadGuardModule(Module):
    name = "bad"

    def configure(self, app: FastAPI, config: Config) -> None:
        from src.core.router import guard

        @app.get("/api/bad/x")
        @guard("nope")
        async def _x():
            return {}


@pytest.mark.pure
def test_unknown_guard_kind_raises_on_build():
    with pytest.raises(RuntimeError, match="не зарегистрированы"):
        create_app(
            modules=[AuthStubModule(), _BadGuardModule()],
            config=Config(server_enabled=True),
        )


@pytest.mark.pure
def test_server_disabled_still_registers_tasks():
    """Режим scheduler-only: configure() (и регистрация задач) выполняется всегда."""
    app = create_app(modules=[_StubModule()], config=Config(server_enabled=False))
    paths = [r.path for r in app.routes if hasattr(r, "path")]
    # роут стаба добавлен в configure напрямую (не в зоне) — он есть даже без API-зоны;
    # ключевое: configure вызвался (задачи бы зарегистрировались тем же путём).
    assert "/api/stub/ping" in paths


@pytest.mark.db
async def test_lifespan_initializes_db(config: Config):
    from src.core.database import get_engine

    app = create_app(modules=[AuthStubModule()], config=config)
    async with app.router.lifespan_context(app):
        assert get_engine() is not None
    assert get_engine() is None


@pytest.mark.db
async def test_module_router_reachable_via_lifespan(config: Config):
    from httpx import ASGITransport, AsyncClient

    app = create_app(modules=[AuthStubModule(), _StubModule()], config=config)
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            r = await c.get("/api/stub/ping")
            assert r.status_code == 200
            assert r.json() == {"ok": True}


# ── зона mcp (смонтированные FastMCP-серверы) ────────────────────────────
# Модули отдают MCP-серверы декларативно (mcp_servers: code → конструктор) +
# поставляют резолвер токена (mcp_token_resolver). Ядро строит McpServerContext,
# монтирует каждый сервер как ASGI-подприложение под /mcp/<code> и композирует
# их lifespan-ы. См. src/core/mcp/, src/core/router/mcp.py.


def _stub_mcp_server(ctx):
    """Минимальный MCP-сервер-заглушка через ядровую фабрику make_mcp_server."""
    from src.core.mcp import make_mcp_server

    mcp = make_mcp_server("stub", "stub server", ctx)

    @mcp.tool()
    async def ping() -> dict:
        return {"ok": True}

    return mcp


async def _stub_resolver(token: str, scope: str):
    """Резолвер-заглушка (как core_users.resolve_token): валиден только 'good'."""
    return SimpleNamespace(id=1, group="admin") if token == "good" else None


class _McpStubModule(Module):
    """Объявляет MCP-сервер 'stub' + поставляет резолвер токена."""

    name = "mcp_stub"
    mcp_servers = {"stub": _stub_mcp_server}
    mcp_token_resolver = staticmethod(_stub_resolver)


class _McpDupModule(Module):
    """Объявляет тот же code 'stub' (без резолвера) — для проверки коллизии code."""

    name = "mcp_dup"
    mcp_servers = {"stub": _stub_mcp_server}


@pytest.mark.pure
def test_build_guard_registry_has_builtins_and_module_guards():
    """build_guard_registry (router/mounting): встроенные виды + влитые Module.guards."""
    from src.core.router.mounting import build_guard_registry

    registry = build_guard_registry([AuthStubModule()])
    assert registry.has("allow_all")
    assert registry.has("deny_all")
    assert registry.has("auth")  # из AuthStubModule.guards
    assert registry.has("ability")
    assert not registry.has("token")  # ещё не зарегистрирован


def _mount_paths(app) -> list[str]:
    """Пути смонтированных подприложений (Mount) — у них есть .path."""
    return [r.path for r in app.routes if hasattr(r, "path")]


@pytest.mark.pure
def test_mcp_not_mounted_without_provider():
    """Нет модуля с mcp_servers ⇒ ничего под /mcp не монтируется."""
    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    assert not any(p.startswith("/mcp") for p in _mount_paths(app))


@pytest.mark.pure
def test_mcp_mounted_when_module_provides_server():
    """Модуль дал mcp_servers ⇒ сервер смонтирован как подприложение /mcp/<code>."""
    app = create_app(
        modules=[AuthStubModule(), _McpStubModule()],
        config=Config(server_enabled=True),
    )
    assert "/mcp/stub" in _mount_paths(app)


@pytest.mark.pure
def test_mcp_skipped_when_api_disabled():
    """SERVER_ENABLED=false ⇒ MCP-серверы не монтируются даже при наличии mcp_servers."""
    app = create_app(
        modules=[AuthStubModule(), _McpStubModule()],
        config=Config(server_enabled=False),
    )
    assert not any(p.startswith("/mcp") for p in _mount_paths(app))


@pytest.mark.pure
def test_mcp_duplicate_code_raises():
    """Два модуля с одинаковым code ⇒ RuntimeError на сборке (громкий отказ)."""
    with pytest.raises(RuntimeError, match="duplicate mcp server code"):
        create_app(
            modules=[AuthStubModule(), _McpStubModule(), _McpDupModule()],
            config=Config(server_enabled=True),
        )


@pytest.mark.pure
def test_mcp_missing_resolver_raises():
    """Есть mcp_servers, но никто не поставил mcp_token_resolver ⇒ RuntimeError."""
    with pytest.raises(RuntimeError, match="mcp_token_resolver"):
        create_app(
            modules=[AuthStubModule(), _McpDupModule()],
            config=Config(server_enabled=True),
        )


@pytest.mark.db
async def test_mcp_lifespan_composes(config: Config):
    """Смонтированный MCP-сервер: lifespan композируется (session manager поднят)."""
    app = create_app(
        modules=[AuthStubModule(), _McpStubModule()],
        config=config,
    )
    assert "/mcp/stub" in _mount_paths(app)
    async with app.router.lifespan_context(app):
        pass  # вход/выход без ошибок ⇒ http_app().lifespan вошёл в стек


@pytest.mark.db
async def test_mcp_endpoint_served_at_code_root_not_double_mcp(config: Config):
    """Эндпоинт сервера — ровно на /mcp/<code>, НЕ на /mcp/<code>/mcp.

    Регресс: сабап по умолчанию слушает streamable_http_path="/mcp"; без path="/"
    в http_app() реальный эндпоинт уезжает в /mcp/stub/mcp (307→404), а /mcp/stub/
    отдаёт 404 — ровно то, что ловил клиентский probe («Connection Failed»).
    """
    from httpx import ASGITransport, AsyncClient

    app = create_app(modules=[AuthStubModule(), _McpStubModule()], config=config)
    body = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    headers = {"Accept": "application/json, text/event-stream"}
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # На code-root эндпоинт ЖИВ и гейтит auth (401), а не 404.
            at_root = await c.post("/mcp/stub/", json=body, headers=headers)
            assert at_root.status_code == 401
            # Старый ошибочный двойной путь больше не существует.
            doubled = await c.post("/mcp/stub/mcp", json=body, headers=headers)
            assert doubled.status_code == 404
