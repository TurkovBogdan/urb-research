"""Гейт отставшей цепочки: пустая база накатывается сама, отставшая — отдаёт заглушку."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core import scheduler
from src.core.app_factory import create_app
from src.core.app_path import project_root
from src.core.config import Config
from src.core.database import close_database, create_all, init_database, session_scope
from src.core.database.migrations import AlembicRunner
from src.core.module import Module
from src.core.router.degraded import PendingMigrationsGate, degraded_pending, mark_degraded
from tests.core._support import AuthStubModule

_PENDING_REVISION = "stub_pending_001"

_UNAPPLIED_REVISION_SOURCE = f'''"""stub pending revision (never applied by these tests)."""

revision = "{_PENDING_REVISION}"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
'''


class _RouteRecorder:
    """Маршрут, который открыл бы сессию к БД: заглушенный запрос до него не доходит."""

    def __init__(self) -> None:
        self.served: list[str] = []

    async def handle(self) -> dict[str, bool]:
        async with session_scope():
            self.served.append("/api/stub/ping")
        return {"ok": True}


class _StubRouteModule(Module):
    name: ClassVar[str] = "stub_route"

    def __init__(self, recorder: _RouteRecorder) -> None:
        self._recorder = recorder

    def configure(self, app: FastAPI, config: Config) -> None:
        app.add_api_route("/api/stub/ping", self._recorder.handle, methods=["GET"])


class _UnappliedMigrationModule(Module):
    """Модуль, чья единственная ревизия не накатана — ровно «схема отстала от кода»."""

    name: ClassVar[str] = "unapplied"

    def __init__(self, migrations_dir: Path) -> None:
        self.migrations_dir = migrations_dir


def _write_unapplied_revision(tmp_path: Path) -> Path:
    versions = tmp_path / "versions"
    versions.mkdir()
    (versions / f"{_PENDING_REVISION}.py").write_text(_UNAPPLIED_REVISION_SOURCE, encoding="utf-8")
    return versions


def _file_db_config(tmp_path: Path, **over) -> Config:
    return Config(
        db_provider="sqlite",
        db_path=str(tmp_path / "app.sqlite3"),
        server_enabled=True,
        **over,
    )


@pytest.fixture
def started_scheduler(monkeypatch) -> list[Config]:
    """Записывает вызовы scheduler.start вместо подъёма тикера."""
    started: list[Config] = []

    async def _record(config: Config) -> None:
        started.append(config)

    monkeypatch.setattr(scheduler, "start", _record)
    return started


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── пустая база: bootstrap и обычная работа ──────────────────────────────────


@pytest.mark.db
async def test_empty_base_applies_the_chain_and_serves(tmp_path: Path, started_scheduler):
    config = _file_db_config(tmp_path, worker_enabled=True)
    modules = [AuthStubModule()]
    app = create_app(modules=modules, config=config)

    async with app.router.lifespan_context(app):
        assert degraded_pending(app) is None
        async with _client(app) as client:
            health = await client.get("/internal/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert started_scheduler

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    try:
        status = await AlembicRunner(modules=modules).status(engine)
    finally:
        await engine.dispose()
    assert status.up_to_date
    assert status.current_heads


@pytest.mark.db
async def test_tables_without_a_version_row_degrade_instead_of_crashing(
    tmp_path: Path, started_scheduler
):
    """База, собранная когда-то через ``create_all``: таблицы есть, ``alembic_version`` нет.
    Цепочка падает на первом же ``CREATE TABLE`` — lifespan обязан выжить и деградировать."""
    config = _file_db_config(tmp_path, worker_enabled=True)
    engine = await init_database(config)
    await create_all(engine)
    await close_database()

    app = create_app(modules=[AuthStubModule()], config=config)
    async with app.router.lifespan_context(app):
        pending = degraded_pending(app)
        async with _client(app) as client:
            health = await client.get("/internal/health")
            page = await client.get("/research")

    assert pending
    assert health.status_code == 200
    assert health.json() == {"status": "degraded", "pending": pending}
    assert page.status_code == 503
    assert started_scheduler == []


@pytest.mark.db
async def test_second_start_on_a_head_base_changes_nothing(tmp_path: Path, started_scheduler):
    config = _file_db_config(tmp_path)
    modules = [AuthStubModule()]
    bootstrapped = create_app(modules=modules, config=config)
    async with bootstrapped.router.lifespan_context(bootstrapped):
        pass

    app = create_app(modules=modules, config=config)
    async with app.router.lifespan_context(app):
        assert degraded_pending(app) is None
        async with _client(app) as client:
            health = await client.get("/internal/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


# ── отставшая база: заглушка вместо данных ───────────────────────────────────


@pytest.mark.db
async def test_base_behind_the_code_serves_degraded(tmp_path: Path, started_scheduler):
    config = _file_db_config(tmp_path, worker_enabled=True)
    bootstrapped = create_app(modules=[AuthStubModule()], config=config)
    async with bootstrapped.router.lifespan_context(bootstrapped):
        pass
    started_scheduler.clear()

    recorder = _RouteRecorder()
    modules = [
        AuthStubModule(),
        _StubRouteModule(recorder),
        _UnappliedMigrationModule(_write_unapplied_revision(tmp_path)),
    ]
    app = create_app(modules=modules, config=config)

    async with app.router.lifespan_context(app):
        assert degraded_pending(app) == [_PENDING_REVISION]
        async with _client(app) as client:
            page = await client.get("/research")
            api = await client.get("/api/stub/ping")
            health = await client.get("/internal/health")

    assert page.status_code == 503
    assert page.headers["content-type"].startswith("text/html")
    assert _PENDING_REVISION in page.text

    assert api.status_code == 503
    assert api.json()["code"] == "migrations_pending"
    assert api.json()["pending"] == [_PENDING_REVISION]

    assert health.status_code == 200
    assert health.json() == {"status": "degraded", "pending": [_PENDING_REVISION]}

    assert recorder.served == []
    assert started_scheduler == []


@pytest.mark.db
async def test_stub_route_does_open_a_session_when_healthy(tmp_path: Path, started_scheduler):
    """Контроль к предыдущему тесту: тот же маршрут на живой базе доходит до сессии."""
    config = _file_db_config(tmp_path)
    recorder = _RouteRecorder()
    app = create_app(modules=[AuthStubModule(), _StubRouteModule(recorder)], config=config)

    async with app.router.lifespan_context(app):
        async with _client(app) as client:
            response = await client.get("/api/stub/ping")

    assert response.status_code == 200
    assert recorder.served == ["/api/stub/ping"]


@pytest.mark.db
async def test_degraded_start_does_not_touch_the_chain(tmp_path: Path, started_scheduler):
    """Заглушка — не «накати молча»: ревизия остаётся неприменённой."""
    config = _file_db_config(tmp_path)
    bootstrapped = create_app(modules=[AuthStubModule()], config=config)
    async with bootstrapped.router.lifespan_context(bootstrapped):
        pass

    modules = [AuthStubModule(), _UnappliedMigrationModule(_write_unapplied_revision(tmp_path))]
    app = create_app(modules=modules, config=config)
    async with app.router.lifespan_context(app):
        pass

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(config.database_url, **config.engine_kwargs)
    try:
        status = await AlembicRunner(modules=modules).status(engine)
    finally:
        await engine.dispose()
    assert [revision.revision for revision in status.pending] == [_PENDING_REVISION]


# ── поверхность гейта (без БД) ───────────────────────────────────────────────


def _degraded_app() -> FastAPI:
    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    mark_degraded(app, [_PENDING_REVISION])
    return app


@pytest.mark.pure
def test_gate_is_the_outermost_middleware():
    """add_middleware вставляет в позицию 0 ⇒ добавленный последним отрабатывает первым."""
    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    assert app.user_middleware[0].cls is PendingMigrationsGate


@pytest.mark.pure
@pytest.mark.skipif(
    not (project_root() / "web" / "dist" / "index.html").is_file(),
    reason="SPA не собрана — mount_spa не вешает middleware, порядок проверять не на чем",
)
async def test_degraded_stub_wins_over_the_spa():
    """SPA-middleware отдала бы index.html на любой GET вне API-префиксов — гейт раньше."""
    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    async with _client(app) as client:
        served = await client.get("/research")
    assert served.status_code == 200
    assert "<html" in served.text.lower()

    mark_degraded(app, [_PENDING_REVISION])
    async with _client(app) as client:
        stub = await client.get("/research")
    assert stub.status_code == 503
    assert _PENDING_REVISION in stub.text


@pytest.mark.pure
@pytest.mark.parametrize("path", ["/api/anything", "/mcp/research", "/storage/file.png"])
async def test_machine_zones_get_json(path: str):
    app = _degraded_app()
    async with _client(app) as client:
        response = await client.get(path)
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["pending"] == [_PENDING_REVISION]


@pytest.mark.pure
async def test_health_stays_exempt_and_answers_200():
    app = _degraded_app()
    async with _client(app) as client:
        response = await client.get("/internal/health")
    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "pending": [_PENDING_REVISION]}


@pytest.mark.pure
async def test_other_internal_routes_are_refused():
    app = _degraded_app()
    async with _client(app) as client:
        response = await client.get("/internal/core/settings/modules")
    assert response.status_code == 503


@pytest.mark.pure
async def test_healthy_app_health_body_unchanged():
    app = create_app(modules=[AuthStubModule()], config=Config(server_enabled=True))
    async with _client(app) as client:
        response = await client.get("/internal/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
