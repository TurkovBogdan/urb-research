"""Монтаж HTTP-зон ядра на FastAPI-приложение.

Вынесено из ``app_factory``: сборка общего реестра guard'ов (``build_guard_registry``)
и монтаж зон под их зон-guard'ами с валидацией видов (``mount_router_zones``).

Разделение ответственности по условиям подключения:
- ``create_app`` решает, монтировать ли HTTP-поверхность ВООБЩЕ (гейт
  ``SERVER_ENABLED``) — это видно прямо из фабрики;
- ``mount_router_zones`` решает, КАКИЕ зоны и при КАКИХ условиях монтируются —
  каждое условие прописано здесь явно (internal — всегда; mcp — отдельные
  ASGI-подприложения через ``mount_mcp_servers``; api/webhook — пока выключены).

``_attach_zone`` — чистая механика монтажа одной зоны, без условий.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI

from src.core.config import Config
from src.core.loggers import get_logger
from src.core.module import Module
from src.core.router import (
    GuardRegistry,
    guard_allow_all,
    guard_deny_all,
    make_zone_guard,
    validate_guard_rules,
)
from src.core.router.internal import (
    INTERNAL_DEFAULT_GUARDS,
    INTERNAL_PREFIX,
    build_internal_zone,
    make_request_delay,
)
from src.core.router.mcp import mount_mcp_servers
from src.core.router.spa import mount_spa
from src.core.router.storage import (
    STORAGE_DEFAULT_GUARDS,
    STORAGE_PREFIX,
    build_storage_zone,
)

_LOG = get_logger()


def build_guard_registry(modules: Sequence[Module]) -> GuardRegistry:
    """Собрать общий реестр guard'ов: встроенные ядра + виды модулей.

    Ядро держит только ``allow_all``/``deny_all``; реальные ``auth``/``ability`` дал бы
    auth-модуль через декларативный ``Module.guards``. Без него умолчание зоны internal —
    встроенный ``allow_all`` (см. ``INTERNAL_DEFAULT_GUARDS``).
    """
    registry = GuardRegistry()
    registry.add("allow_all", guard_allow_all)
    registry.add("deny_all", guard_deny_all)
    for m in modules:
        for kind, fn in m.guards.items():
            registry.add(kind, fn)
    return registry


def _attach_zone(
    app: FastAPI,
    registry: GuardRegistry,
    zone: APIRouter,
    prefix: str,
    default_guards: list[str],
    *,
    extra_deps: Sequence[Any] = (),
) -> None:
    """Механика монтажа ОДНОЙ зоны (без условий — их решает ``mount_router_zones``):
    зон-guard (+ необязательные ``extra_deps``) → ``include_router`` под префиксом →
    валидация, что все упомянутые виды зарегистрированы."""
    deps = [Depends(make_zone_guard(registry, default=default_guards)), *extra_deps]
    app.include_router(zone, prefix=prefix, dependencies=deps)
    validate_guard_rules(app, registry, defaults=default_guards)


def mount_router_zones(
    app: FastAPI, modules: Sequence[Module], config: Config
) -> list[AbstractAsyncContextManager[None]]:
    """Смонтировать HTTP-зоны на ``app``. Условие подключения КАЖДОЙ зоны — здесь, явно.

    Зовётся из ``create_app`` под гейтом ``SERVER_ENABLED`` (сам гейт виден в фабрике).
    Возвращает lifespan-CM смонтированных MCP-серверов — ``create_app`` композирует
    их в свой lifespan (иначе session manager форка не поднимется).
    """
    registry = build_guard_registry(modules)

    # internal — монтируется ВСЕГДА (ядро + SPA). DEBUG: искусственная задержка идёт
    # ПОСЛЕ guard'а (отклонённые запросы не ждут), добавляется только при ms > 0.
    internal_extra: list[Any] = []
    if config.server_debug_delay_ms > 0:
        internal_extra.append(Depends(make_request_delay(config.server_debug_delay_ms)))
        _LOG.warning(
            "mount_router_zones: SERVER_DEBUG_DELAY_MS=%d — internal API искусственно "
            "замедлён на %d мс/запрос (DEBUG; в проде держать 0)",
            config.server_debug_delay_ms,
            config.server_debug_delay_ms,
        )
    _attach_zone(
        app,
        registry,
        build_internal_zone(modules),
        INTERNAL_PREFIX,
        INTERNAL_DEFAULT_GUARDS,
        extra_deps=internal_extra,
    )

    # storage — отдача файлов от корня /storage (guard auth). Только protected ходит
    # сюда; public отдаёт nginx напрямую, private закрыт. Монтируется всегда.
    _attach_zone(
        app,
        registry,
        build_storage_zone(modules),
        STORAGE_PREFIX,
        STORAGE_DEFAULT_GUARDS,
    )

    # spa — собранный фронт из web/dist отдаёт тот же HTTP-сервер. Это middleware
    # (вне зон/guard'ов): короткозамыкает любой GET вне API-префиксов до роутинга,
    # поэтому порядок монтажа не важен. Нет сборки → no-op (см. mount_spa).
    mount_spa(app)

    # mcp — каждый MCP-сервер модуля монтируется как отдельное ASGI-подприложение
    # (форк fastmcp, Streamable HTTP) под /mcp/<code>; auth — внутри сервера
    # (McpServerTokenVerifier), НЕ зон-guard'ом (mount обходит dependencies).
    # Возвращённые lifespan-ы поднимаются в create_app.
    mcp_lifespans = mount_mcp_servers(app, modules, config)

    # api / webhook — болванки, пока НЕ монтируются (guard-виды scope/signature ещё
    # не реализованы; см. router/api.py, router/webhook.py).
    return mcp_lifespans


__all__ = ["build_guard_registry", "mount_router_zones"]
