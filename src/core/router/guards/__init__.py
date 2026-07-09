"""Подсистема защиты маршрутов: реестр guard'ов + встроенные виды + метка ``@guard``.

Guard — FastAPI-зависимость ``async (request) -> None``, прерывающая запрос через
``raise`` (``ApiError``); её форма — тип ``GuardFn``. Имя функции-реализации =
``guard_`` + вид. Состав подпакета:

- ``registry`` — ``GuardRegistry`` (``вид → GuardFn``) + тип ``GuardFn``;
- ``universal`` — встроенная пара ядра ``guard_allow_all``/``guard_deny_all``;
- ``enforce`` — навешивание guard'ов на маршруты: метка ``@guard`` + зон-guard
  (исполнитель) + валидация видов на сборке.

Реальные ``auth``/``ability`` (CASL) живут в ``core_users`` и вливаются в реестр из
декларативного ``Module.guards``; ядро держит лишь ``allow_all``/``deny_all``.
"""

from __future__ import annotations

from src.core.router.guards.enforce import (
    guard,
    guard_rules,
    is_allow_all,
    is_deny_all,
    make_zone_guard,
    validate_guard_rules,
)
from src.core.router.guards.registry import GuardFn, GuardRegistry
from src.core.router.guards.universal import guard_allow_all, guard_deny_all

__all__ = [
    "GuardFn",
    "GuardRegistry",
    "guard",
    "guard_allow_all",
    "guard_deny_all",
    "guard_rules",
    "is_allow_all",
    "is_deny_all",
    "make_zone_guard",
    "validate_guard_rules",
]
