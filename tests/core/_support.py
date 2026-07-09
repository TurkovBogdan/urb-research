"""Тестовые помощники ядра.

``auth``/``ability`` больше не моки ядра — их даёт ``core_users``. Чтобы core-тесты
монтировали зону internal (умолчание ``["auth"]``) без подъёма всего ``core_users``
с его БД, подкладываем лёгкий stub-модуль: ``auth`` кладёт фиктивного админа,
``ability`` пропускает всё.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import ClassVar

from fastapi import Request

from src.core.module import Module

# Ядро о принципале ничего не знает (duck-typed request.state.user); модель — у
# core_users. Тестам ядра достаточно объекта нужной формы.
_STUB_USER = SimpleNamespace(
    id=1, email="admin@semaphore.local", name="admin", group="admin", is_active=True
)


async def _stub_auth(request: Request) -> None:
    request.state.user = _STUB_USER


async def _stub_ability(request: Request) -> None:
    return


class AuthStubModule(Module):
    """Passthrough ``auth``/``ability`` для тестов зоны internal (декларативно)."""

    name: ClassVar[str] = "auth_stub"
    guards = {"auth": _stub_auth, "ability": _stub_ability}


__all__ = ["AuthStubModule"]
