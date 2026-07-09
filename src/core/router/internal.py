"""Зона ``internal`` — сборка агрегирующего роутера (монтируется на ``/internal``).

Состав зоны: публичный ``/health`` + эндпоинты ядра (``/core/settings``) +
под-роутеры модулей (``Module.internal_router``/``internal_router_prefix``).

Зона строится СВЕЖЕЙ на каждый ``create_app`` (``build_internal_zone`` возвращает
новый ``APIRouter``) — без глобального синглтона, иначе повторные ``create_app`` в
тестах копили бы маршруты. Защиту вешает ``mount_router_zones`` (``router/mounting.py``)
зон-guard'ом (``make_zone_guard(registry, default=INTERNAL_DEFAULT_GUARDS)``); здесь —
только состав.

``api``/``webhook`` — отдельные зоны-болванки рядом (``api.py``/``webhook.py``), пока не смонтированы.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence

from fastapi import APIRouter

from src.core.settings.api import router as settings_router
from src.core.module import Module
from src.core.router.guards import guard

# Префикс монтажа зоны и её умолчательные виды guard'ов (default-on).
# Чистое ядро auth-модуля не имеет, поэтому умолчание — встроенный ``allow_all``.
# Когда добавится провайдер auth (свой ``Module.guards`` с видом ``auth``), вернуть сюда ``["auth"]``.
INTERNAL_PREFIX = "/internal"
INTERNAL_DEFAULT_GUARDS = ["allow_all"]


def make_request_delay(ms: int) -> Callable[[], Awaitable[None]]:
    """DEBUG-only зон-зависимость: тормозит каждый запрос зоны на ``ms`` миллисекунд.

    Для отладки фронта (скелетоны/лоадеры). Монтируется только при ``ms > 0`` (см.
    ``mount_router_zones`` в ``router/mounting.py``) — в проде нулевой оверхед.
    Вешается ПОСЛЕ guard'а, поэтому отклонённые (401) запросы не ждут впустую.
    """
    seconds = ms / 1000

    async def _delay() -> None:
        await asyncio.sleep(seconds)

    return _delay


@guard("allow_all")
async def _health() -> dict[str, str]:
    """Публичный liveness зоны internal (без auth). Доступен только при
    смонтированной зоне ⇒ отражает, что API реально поднят (SERVER_ENABLED)."""
    return {"status": "ok"}


def build_internal_zone(modules: Sequence[Module]) -> APIRouter:
    """Свежий агрегатор зоны internal: health + ядро + под-роутеры модулей."""
    zone = APIRouter()
    zone.add_api_route("/health", _health, methods=["GET"], tags=["core"])
    zone.include_router(settings_router, prefix="/core/settings", tags=["core"])
    for m in modules:
        if m.internal_router is not None:
            zone.include_router(
                m.internal_router, prefix=m.internal_router_prefix, tags=[m.name]
            )
    return zone


__all__ = [
    "INTERNAL_DEFAULT_GUARDS",
    "INTERNAL_PREFIX",
    "build_internal_zone",
    "make_request_delay",
]
