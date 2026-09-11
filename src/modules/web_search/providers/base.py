"""Базовые классы провайдеров — две независимые роли движка поверх коннекторов ``core_connectors``.

Каждый движок работает через коннектор, который открывается по коду сервиса
(``open_connector``): ключ, адрес и включённость живут в записи доступа, а не здесь.
``available()`` спрашивает у модуля доступов, готова ли запись (есть, включена, заполнена) —
реестр по этому признаку отдаёт список доступных провайдеров. Две функции внешнего веба,
у каждой свой выбор провайдера:
- ``SearchEngine`` — поиск: ``search(request)`` → список ссылок
  ``[{url, rank?, score?, summary?, title?, meta?}]`` (контент НЕ тянет; ``summary`` — краткое
  содержание в контексте запроса, ``title`` — заголовок документа, ``meta`` — остаточные
  контекстные поля движка). Умеют Tavily, Firecrawl, Grok (xAI).
- ``FetchEngine`` — получение контента: ``fetch_pages(urls)`` → ``{url: markdown|None}``,
  батч до ``pages_per_request`` url. Умеют Tavily, Firecrawl, daemon-web-scrapper (Grok — нет).

Роли независимы (общего предка нет). Один провайдер может реализовать обе (Tavily/Firecrawl)
и зарегистрироваться в обоих реестрах. Оркестрацию (поиск → сохранить ссылки → фетч
контента → статусы) держит синхронный сервис ``services/searcher.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from src.modules.core_connectors.service import access_available
from src.modules.web_search.providers.request import SearchRequest


class SearchEngine(ABC):
    """Движок поиска: по запросу возвращает ссылки (без контента страниц).

    ``code`` совпадает с кодом коннектора в ``core_connectors`` — это и есть привязка
    потребителя к сервису; ``available()`` спрашивает готовность его записи доступа.
    """

    code: ClassVar[str]

    async def available(self) -> bool:
        """Готов ли доступ к сервису: запись есть, включена и заполнена (без сети)."""
        return await access_available(self.code)

    @abstractmethod
    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        """Запрос к движку → ``[{url, rank?, score?, summary?, title?, meta?}]`` (только ссылки)."""


class FetchEngine(ABC):
    """Движок получения контента: по url'ам возвращает markdown.

    ``code`` совпадает с кодом коннектора в ``core_connectors``; ``available()`` спрашивает
    готовность его записи доступа.
    """

    code: ClassVar[str]
    pages_per_request: ClassVar[int] = 1  # сколько url движок берёт за один запрос контента

    async def available(self) -> bool:
        """Готов ли доступ к сервису: запись есть, включена и заполнена (без сети)."""
        return await access_available(self.code)

    @abstractmethod
    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        """Батч-получение контента: ``{url: markdown|None}`` для всех переданных url."""


__all__ = ["SearchEngine", "FetchEngine"]
