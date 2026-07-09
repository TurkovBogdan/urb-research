"""Реестры движков: по классу на роль — поиск и получение контента.

Две роли — два реестра (провайдер, умеющий обе, регистрируется в обоих). Реестр учитывает
доступность провайдера через ``core_connectors``: ``available_codes()``/``is_available(code)``
опираются на ``available()`` движка (коннектор можно выключить в настройках). Активный движок
берёт синхронный сервис поиска: ``search_engines.get(code)`` / ``fetch_engines.get(code)``.
"""

from __future__ import annotations

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

    def available_codes(self) -> list[str]:
        """Коды провайдеров, чей коннектор ``core_connectors`` включён."""
        return sorted(code for code, engine in self._engines.items() if engine.available())

    def is_available(self, code: str) -> bool:
        """Доступен ли провайдер ``code`` (его коннектор включён в настройках)."""
        return self.get(code).available()


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
