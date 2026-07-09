"""Зона ``api`` — внешний токенный API (БОЛВАНКА; пока НЕ смонтирована).

Параллель ``src/core/router/internal.py`` для зоны ``/api``: сторонние интеграции
по bearer-токену + scope. Состав — под-роутеры модулей (``Module.api_router``);
защита — зон-guard с умолчанием ``API_DEFAULT_GUARDS``.

Чтобы включить (TODO):
1. Реализовать и зарегистрировать guard вида ``scope`` (``Security`` + OAuth2 scopes;
   см. AGENTS/docs/router.md «Как добавить новый вид guard'а»).
2. Дать модулям под-роутер ``api_router`` / ``api_router_prefix`` (как ``internal_router``;
   добавить classvar в ``src/core/module.py``).
3. Смонтировать в ``create_app`` под флагом (как зону internal):
   ``app.include_router(build_api_zone(modules), prefix=API_PREFIX,
   dependencies=[Depends(make_zone_guard(registry, default=API_DEFAULT_GUARDS))])``
   + ``validate_guard_rules(...)``.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter

from src.core.module import Module

API_PREFIX = "/api"
API_DEFAULT_GUARDS = ["scope"]  # TODO: guard вида "scope" ещё не реализован/не зарегистрирован


def build_api_zone(modules: Sequence[Module]) -> APIRouter:
    """БОЛВАНКА: свежий агрегатор зоны api из ``api_router`` модулей.

    Пока у ``Module`` нет ``api_router`` — берём через ``getattr`` (зона выйдет
    пустой). После добавления classvar заработает как ``build_internal_zone``.
    """
    zone = APIRouter()
    for m in modules:
        router = getattr(m, "api_router", None)
        if router is not None:
            zone.include_router(
                router, prefix=getattr(m, "api_router_prefix", ""), tags=[m.name]
            )
    return zone


__all__ = ["API_DEFAULT_GUARDS", "API_PREFIX", "build_api_zone"]
