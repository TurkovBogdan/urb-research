"""Реестры движков: по классу на роль — поиск и получение контента.

Две роли — два реестра (провайдер, умеющий обе, регистрируется в обоих). Доступность
провайдера — вопрос к модулю доступов: ``available_codes()``/``is_available(code)`` идут в
``core_connectors`` за готовностью записи, поэтому они асинхронные (запись живёт в базе).
Активный движок берёт синхронный сервис поиска: ``search_engines.get(code)`` /
``fetch_engines.get(code)``.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar, Generic, TypeVar

from src.modules.web_search.providers.base import FetchEngine, SearchEngine

E = TypeVar("E", SearchEngine, FetchEngine)


class EngineRegistry(Generic[E]):
    """Реестр движков одной роли: регистрация, выбор и учёт доступности провайдеров."""

    role: ClassVar[str]

    def __init__(self) -> None:
        self._engines: dict[str, E] = {}

    def register(self, engine: E) -> E:
        self._engines[engine.code] = engine
        return engine

    def get(self, code: str) -> E:
        try:
            return self._engines[code]
        except KeyError:
            raise KeyError(f"Unknown {self.role} engine: {code!r}")

    def codes(self) -> list[str]:
        """Все зарегистрированные коды (без учёта доступности)."""
        return sorted(self._engines)

    async def available_codes(self) -> list[str]:
        """Коды провайдеров, чья запись доступа в ``core_connectors`` готова к работе."""
        codes = self.codes()
        ready = await asyncio.gather(*(self._engines[code].available() for code in codes))
        return [code for code, is_ready in zip(codes, ready) if is_ready]

    async def is_available(self, code: str) -> bool:
        """Доступен ли провайдер ``code`` (его запись доступа готова)."""
        return await self.get(code).available()


class SearchEngineRegistry(EngineRegistry[SearchEngine]):
    role = "search"


class FetchEngineRegistry(EngineRegistry[FetchEngine]):
    role = "fetch"


search_engines = SearchEngineRegistry()
fetch_engines = FetchEngineRegistry()


__all__ = [
    "EngineRegistry",
    "SearchEngineRegistry",
    "FetchEngineRegistry",
    "search_engines",
    "fetch_engines",
]
