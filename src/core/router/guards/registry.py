"""Общий реестр guard'ов: ``вид → guard``. НЕ разделён по зонам.

``GuardFn`` — форма callable'а guard'а: FastAPI-зависимость
``async (request) -> None``, прерывающая запрос через ``raise`` (``ApiError``).
Реестр строится один раз при сборке ``create_app`` (ядро предрегистрирует
``allow_all``/``deny_all``, модули добавляют свои через декларативный
``Module.guards``) и дальше не мутируется. ``@guard("вид")`` ссылается на guard по
имени; зарегистрированный guard работает в любой зоне.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request

GuardFn = Callable[[Request], Awaitable[None]]


class GuardRegistry:
    """Плоский реестр ``вид → GuardFn`` (без зонной привязки)."""

    def __init__(self) -> None:
        self._guards: dict[str, GuardFn] = {}

    def add(self, kind: str, fn: GuardFn) -> None:
        """Зарегистрировать guard под видом. Повторная регистрация — ошибка."""
        if kind in self._guards:
            raise ValueError(f"guard '{kind}' уже зарегистрирован")
        self._guards[kind] = fn

    def has(self, kind: str) -> bool:
        return kind in self._guards

    def resolve(self, kind: str) -> GuardFn:
        return self._guards[kind]


__all__ = ["GuardFn", "GuardRegistry"]
