"""Два встроенных универсальных guard'а ядра — пара ``allow_all``/``deny_all``.

Реальные ``auth``/``ability`` (CASL) пришли бы из auth-модуля через декларативный
``Module.guards``; ядро держит лишь эту пару. Имена функций =
``guard_`` + вид (``guard_<вид>``), под которым guard лежит в реестре.

- ``allow_all`` (``guard_allow_all``) — «всё разрешает» (пропускает всех). Снимает
  защиту зоны для конкретного маршрута через метку ``@guard("allow_all")`` (login).
- ``deny_all`` (``guard_deny_all``) — «всё кладёт» (блокирует всех). Двояко: явной
  меткой ``@guard("deny_all")`` (намеренно выключить маршрут) и как **фолбэк**
  зон-guard'а, когда у маршрута не набралось ни умолчания зоны, ни меток —
  secure-by-default.
"""

from __future__ import annotations

from fastapi import Request

from src.core.api.errors import ApiError


async def guard_allow_all(request: Request) -> None:
    return


async def guard_deny_all(request: Request) -> None:
    raise ApiError.unauthorized("Маршрут закрыт (нет guard)")


__all__ = ["guard_allow_all", "guard_deny_all"]
