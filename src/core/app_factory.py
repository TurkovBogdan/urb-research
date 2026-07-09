"""Application factory: собирает FastAPI-приложение из набора модулей.

Минимальная фабрика — БД, settings, регистрация модулей. Состав HTTP-зоны
``internal`` (включая публичный ``/health``) — в ``src/core/router/internal.py``;
web-специфика (CORS, статика) — в ``apps/<name>/server.py``.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from src.core import scheduler
from src.core.settings.bootstrap import (
    load_initial_stores,
    register_settings_schemas,
)
from src.core.settings.registry import get_registry as get_settings_registry
from src.core.api import register_exception_handlers
from src.core.config import Config
from src.core.database import close_database, create_all, init_database
from src.core.database.migrations import AlembicRunner
from src.core.loggers import get_logger
from src.core.module import Module
from src.core.router.mounting import mount_router_zones
from src.core.scheduler.registry import get_registry
from src.core.tasks import register as register_core_tasks

_LOG = get_logger()


def create_app(modules: Sequence[Module], config: Config) -> FastAPI:
    """Собрать FastAPI-приложение из явного списка модулей."""

    # Lifespan-ы смонтированных MCP-серверов: заполняются в build phase ниже
    # (mount_router_zones) и композируются здесь через AsyncExitStack. Late-binding
    # замыкания: closure читает имя на старте, уже после build phase.
    mcp_lifespans: list[AbstractAsyncContextManager[None]] = []

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _LOG.info("lifespan: startup, modules=%s", [m.name for m in modules])
        engine = await init_database(config)
        if config.sqlite_in_memory:
            # Только in-memory SQLite (тесты, StaticPool в одном коннекте) строит схему
            # из моделей — у неё нет истории миграций и она живёт один прогон. Файловые
            # БД (dev-sqlite и postgres) всегда идут через Alembic.
            await create_all(engine)
            _LOG.info("lifespan: in-memory sqlite — schema built from models (create_all)")
        elif config.db_auto_migrate:
            await AlembicRunner(modules=modules).upgrade_head(engine)
        else:
            _LOG.warning(
                "lifespan: auto_migrate disabled (DB_AUTO_MIGRATE=false) — "
                "skipping Alembic upgrade; apply migrations manually (app.py migrate upgrade)"
            )
        await load_initial_stores(modules)
        for m in modules:
            try:
                await m.on_startup(app)
            except Exception as exc:  # noqa: BLE001
                _LOG.exception("lifespan: %s.on_startup raised %s", m.name, exc)
        # Поднять session-manager'ы MCP-серверов (форк инициализирует их в lifespan
        # своего http_app); закрываются автоматически на выходе из стека.
        async with AsyncExitStack() as mcp_stack:
            for cm in mcp_lifespans:
                await mcp_stack.enter_async_context(cm)
            await scheduler.start(config)
            try:
                yield
            finally:
                _LOG.info("lifespan: shutdown")
                await scheduler.stop()
                for m in reversed(list(modules)):
                    try:
                        await m.shutdown(app)
                    except Exception as exc:  # noqa: BLE001
                        _LOG.exception(
                            "lifespan: %s.shutdown raised %s", m.name, exc
                        )
                await close_database()

    # Swagger/OpenAPI ОТКЛЮЧЕНЫ: API внутренний, схему наружу не публикуем (FastAPI
    # по умолчанию включил бы /docs + /openapi.json). Гейт SERVER_ENABLED — ниже.
    app = FastAPI(
        title="Semaphore.Core",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.module_configs = {
        m.name: m.config_cls() for m in modules if m.config_cls is not None
    }
    get_registry().clear()
    get_settings_registry().clear()
    register_core_tasks()
    register_exception_handlers(app)

    # ── build phase ─────────────────────────────────────────────────────
    # configure() выполняется ВСЕГДА: регистрирует scheduler-задачи (нужны и в
    # режиме «только scheduler»). Монтаж HTTP-поверхности — отдельно, под флагом.
    register_settings_schemas(modules)
    for m in modules:
        m.configure(app, config)

    # ── HTTP-поверхность: гейт SERVER_ENABLED (виден прямо здесь) ───────
    # ВКЛ/ВЫКЛ всей поверхности — это условие; какие зоны и при каких условиях
    # монтируются — в mount_router_zones (src/core/router/mounting.py).
    if config.server_enabled:
        mcp_lifespans = mount_router_zones(app, modules, config)
    else:
        _LOG.info(
            "create_app: SERVER_ENABLED=false — API-поверхность ядра не "
            "смонтирована (режим worker-only)"
        )

    return app


__all__ = ["create_app"]
