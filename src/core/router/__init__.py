"""Маршрутизация ядра: зоны + подсистема защиты ``guards``.

Зона = префиксное пространство роутеров поверх общего реестра guard'ов. Сам
зон-агрегатор собирается СВЕЖИМ в ``create_app`` (без глобального синглтона —
иначе повторные ``create_app`` в тестах копили бы маршруты). Состав пакета:
``guards/`` (подсистема защиты: реестр + встроенные ``allow_all``/``deny_all`` +
метка ``@guard``) и зоны ``internal``/``api``/``webhook``. Активна зона
``internal``; ``api``/``webhook`` — позже. Guard-поверхность реэкспортится сюда
из подпакета ``guards`` единой точкой.
"""

from __future__ import annotations

from src.core.router.guards import (
    GuardFn,
    GuardRegistry,
    guard,
    guard_allow_all,
    guard_deny_all,
    guard_rules,
    is_allow_all,
    is_deny_all,
    make_zone_guard,
    validate_guard_rules,
)

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
