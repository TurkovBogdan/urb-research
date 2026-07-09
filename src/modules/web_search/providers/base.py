"""Базовые классы провайдеров — две независимые роли движка поверх коннекторов ``core_connectors``.

Каждый движок обёрнут вокруг коннектора ``core_connectors``, который можно выключить в настройках
(``*_gateway_enabled``): ``available()`` читает этот тумблер — реестр по нему отдаёт список
доступных провайдеров. Две функции внешнего веба, у каждой свой выбор провайдера:
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

from src.modules.core_connectors.settings import service_enabled
from src.modules.web_search.providers.request import SearchRequest


class SearchEngine(ABC):
    """Движок поиска: по запросу возвращает ссылки (без контента страниц).

    Провайдер задаёт ``code`` и ``enabled_field`` (= ``ENABLED_FIELD`` его коннектора
    ``core_connectors``); ``available()`` читает этот тумблер (выключен → провайдер недоступен).
    """

    code: ClassVar[str]
    enabled_field: ClassVar[str]

    def available(self) -> bool:
        """Доступен ли провайдер: его коннектор ``core_connectors`` включён в настройках."""
        return service_enabled(self.enabled_field)

    @abstractmethod
    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        """Запрос к движку → ``[{url, rank?, score?, summary?, title?, meta?}]`` (только ссылки)."""


class FetchEngine(ABC):
    """Движок получения контента: по url'ам возвращает markdown.

    Провайдер задаёт ``code`` и ``enabled_field`` (= ``ENABLED_FIELD`` его коннектора
    ``core_connectors``); ``available()`` читает этот тумблер (выключен → провайдер недоступен).
    """

    code: ClassVar[str]
    enabled_field: ClassVar[str]
    pages_per_request: ClassVar[int] = 1  # сколько url движок берёт за один запрос контента

    def available(self) -> bool:
        """Доступен ли провайдер: его коннектор ``core_connectors`` включён в настройках."""
        return service_enabled(self.enabled_field)

    @abstractmethod
    async def fetch_pages(self, urls: list[str]) -> dict[str, str | None]:
        """Батч-получение контента: ``{url: markdown|None}`` для всех переданных url."""


__all__ = ["SearchEngine", "FetchEngine"]
