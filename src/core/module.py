"""Контракт модуля: что модуль предоставляет ядру.

Module — провайдер-класс с явными lifecycle-хуками. Заменяет dataclass
``ModuleSpec`` + одиночный ``register`` callable: для каждой фазы — именованный
метод, который ядро вызывает в нужный момент.

Фазы:
- ``configure(app, config)`` — sync, build phase в ``create_app``. Регистрирует
  роутеры, scheduler-задачи, sync-ресурсы с безопасными дефолтами. DB ещё нет.
- ``on_settings_change(store)`` — sync, фаза runtime. Срабатывает на первичный
  install store (lifespan startup) и на каждый PUT/reset через API.
- ``on_startup(app)`` — async, после всех модулей + DB + миграций + settings.
  Здесь можно делать async-инициализацию: seed данных, регистрация агентов и т.п.
- ``shutdown(app)`` — async, lifespan finally (в обратном порядке).

Все хуки имеют пустые дефолты на базовом классе — модули переопределяют то,
что им нужно. ``name`` — единственный обязательный атрибут.
"""

from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from fastapi import APIRouter, FastAPI
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from src.core.settings.schema import ModuleSchema
    from src.core.config import Config
    from src.core.mcp import McpServerBuilder, TokenResolver
    from src.core.module_state import ModuleStore
    from src.core.router import GuardFn


class Module(ABC):
    """Базовый класс модуля приложения."""

    # ── declarative attributes (class-level) ─────────────────────────────
    name: ClassVar[str]
    # Человекочитаемое описание назначения модуля (проза). Наружу — в settings-API
    # ``/modules`` для карточки на ``/core/settings``; ``name`` остаётся тех. кодом.
    description: ClassVar[str] = ""
    migrations_dir: ClassVar[Path | None] = None
    config_cls: ClassVar[type[BaseSettings] | None] = None
    settings_schema: ClassVar["ModuleSchema | None"] = None
    # Guard'ы модуля (``вид → guard``); ядро вливает их в общий реестр до монтажа
    # зон (``_build_guard_registry``). Реестр общий — вид работает в любой зоне.
    # Пусто у большинства; auth-модуль дал бы ``auth``/``ability``. Объявляются ДО
    # роутеров: guard'ы — это защита, роутеры — защищаемая поверхность (сначала
    # реестр, потом маршруты — тот же порядок, что и в монтаже create_app).
    guards: ClassVar[dict[str, "GuardFn"]] = {}
    # Под-роутер зоны internal. create_app включает его в зон-агрегатор
    # (вместо app.include_router("/internal/<m>") в configure). None — модуль без HTTP.
    # internal_router_prefix — под-префикс внутри зоны internal (напр. "/my-module"); не
    # выводится из name (kebab vs underscore), поэтому задаётся явно. Имя квалифицировано
    # зоной — у будущих api/webhook будут свои (api_router/_prefix, webhook_router/_prefix).
    internal_router: ClassVar[APIRouter | None] = None
    internal_router_prefix: ClassVar[str] = ""
    # Под-роутер зоны storage (отдача файлов от корня ``/storage``). Зеркало
    # internal_router: ядро включает его в зон-агрегатор. None — модуль без
    # файловой поверхности (его поставлял бы storage-модуль).
    storage_router: ClassVar[APIRouter | None] = None
    storage_router_prefix: ClassVar[str] = ""
    # MCP-серверы модуля: ``code -> mcp_server`` (конструктор ``(ctx) -> FastMCP``).
    # Декларативно, зеркало ``guards``: ключ ``code`` = URL-сегмент ``/mcp/<code>``,
    # значение — ФУНКЦИЯ (а не экземпляр), поэтому объявление словаря НЕ импортирует
    # ``fastmcp`` (воркер чист). Модуль может дать несколько серверов; пусто = не-MCP.
    # Монтаж + auth + audit даёт ядро (``mount_mcp_servers``, backend-only).
    mcp_servers: ClassVar[dict[str, "McpServerBuilder"]] = {}
    # Резолвер MCP-токена ``(token, scope) -> принципал | None`` (зеркало ``guards`` —
    # декларативный шов, которым ядро получает резолвер БЕЗ импорта модуля).
    # Ставит auth-модуль (= его ``resolve_token``); собирает
    # ``mount_mcp_servers`` в единственный ``McpServerTokenVerifier``. None — модуль
    # резолвер не поставляет.
    mcp_token_resolver: ClassVar["TokenResolver | None"] = None

    # ── state store ──────────────────────────────────────────────────────
    @property
    def store(self) -> "ModuleStore":
        """Произвольное runtime-состояние модуля (``core_modules_state``).

        Код хранилища — ``self.name``, так что модуль не повторяет свой код:
        ``await self.store.set("import_cursor", {...})``. Для внутренних данных
        (курсоры, счётчики, маркеры), не для пользовательского конфига (тот — в
        settings store). Доступно после инициализации БД (startup/runtime).
        """
        from src.core.module_state import module_store

        return module_store(self.name)

    # ── build phase ──────────────────────────────────────────────────────
    def configure(self, app: FastAPI, config: "Config") -> None:
        """Sync. Регистрация роутеров, scheduler-задач, sync-ресурсов.

        Ресурсы, созданные здесь, ОБЯЗАНЫ быть пригодны в безопасном no-op
        состоянии до первого ``on_settings_change(store)`` в lifespan startup.
        DB ещё нет, settings store тоже.
        """

    # ── settings event ───────────────────────────────────────────────────
    def on_settings_change(self, store: Any) -> None:
        """Sync. Первичный install store (lifespan startup) и каждый PUT/reset.

        Async I/O запрещён. Если нужна async-реакция — ``asyncio.create_task``
        внутри хука или флаг, который подхватит следующий tick планировщика.
        """

    # ── startup phase (async, all modules ready) ──────────────────────────
    async def on_startup(self, app: FastAPI) -> None:
        """Async. Все модули сконфигурированы, DB готова, settings загружены.

        Вызывается один раз в lifespan, до scheduler.start().
        Подходит для seed данных, регистрации агентов и прочей async-инициализации.
        """

    # ── shutdown phase ──────────────────────────────────────────────────
    async def shutdown(self, app: FastAPI) -> None:
        """Перед ``scheduler.stop()`` / ``close_database()``.

        Обратный порядок по списку модулей. Async teardown ресурсов
        (httpx-клиенты, пулы и т.п.).
        """


__all__ = ["Module"]
