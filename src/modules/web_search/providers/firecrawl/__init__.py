"""Движок Firecrawl. Импорт регистрирует его в реестрах поиска и получения контента."""

from src.modules.web_search.providers.firecrawl.client import FirecrawlEngine
from src.modules.web_search.providers.registry import fetch_engines, search_engines

_firecrawl = FirecrawlEngine()
search_engines.register(_firecrawl)
fetch_engines.register(_firecrawl)

__all__ = ["FirecrawlEngine"]
