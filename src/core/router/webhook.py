"""Зона ``webhook`` — входящие вебхуки (БОЛВАНКА; пока НЕ смонтирована).

Параллель ``src/core/router/internal.py`` для зоны ``/webhook``: приём вебхуков от
внешних источников. Состав — под-роутеры модулей (``Module.webhook_router``);
защита — зон-guard с умолчанием ``WEBHOOK_DEFAULT_GUARDS`` (проверка подписи).

Чтобы включить (TODO):
1. Реализовать и зарегистрировать guard вида ``signature`` (валидация подписи источника
   по сырому телу запроса; см. AGENTS/docs/router.md «Как добавить новый вид guard'а»).
   Учесть: guard'у нужно СЫРОЕ тело — на уровне зоны/ASGI-middleware не «съедать» body.
2. Дать модулям под-роутер ``webhook_router`` / ``webhook_router_prefix`` (classvar в
   ``src/core/module.py``).
3. Смонтировать в ``create_app`` под флагом (как зону internal):
   ``app.include_router(build_webhook_zone(modules), prefix=WEBHOOK_PREFIX,
   dependencies=[Depends(make_zone_guard(registry, default=WEBHOOK_DEFAULT_GUARDS))])``
   + ``validate_guard_rules(...)``.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter

from src.core.module import Module

WEBHOOK_PREFIX = "/webhook"
WEBHOOK_DEFAULT_GUARDS = ["signature"]  # TODO: guard вида "signature" ещё не реализован


def build_webhook_zone(modules: Sequence[Module]) -> APIRouter:
    """БОЛВАНКА: свежий агрегатор зоны webhook из ``webhook_router`` модулей.

    Пока у ``Module`` нет ``webhook_router`` — берём через ``getattr`` (зона выйдет
    пустой). После добавления classvar заработает как ``build_internal_zone``.
    """
    zone = APIRouter()
    for m in modules:
        router = getattr(m, "webhook_router", None)
        if router is not None:
            zone.include_router(
                router, prefix=getattr(m, "webhook_router_prefix", ""), tags=[m.name]
            )
    return zone


__all__ = ["WEBHOOK_DEFAULT_GUARDS", "WEBHOOK_PREFIX", "build_webhook_zone"]
