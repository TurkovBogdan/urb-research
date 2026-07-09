"""Провайдеры web_search. Импорт пакетов регистрирует движки поиска и сервисы контента."""

from src.modules.web_search.providers import firecrawl as _firecrawl  # noqa: F401
from src.modules.web_search.providers import tavily as _tavily  # noqa: F401
from src.modules.web_search.providers import web_scrapper as _web_scrapper  # noqa: F401
from src.modules.web_search.providers import xai as _xai  # noqa: F401
from src.modules.web_search.providers.base import FetchEngine, SearchEngine
from src.modules.web_search.providers.registry import fetch_engines, search_engines
from src.modules.web_search.providers.request import SearchRequest

__all__ = [
    "SearchEngine",
    "FetchEngine",
    "SearchRequest",
    "search_engines",
    "fetch_engines",
]
