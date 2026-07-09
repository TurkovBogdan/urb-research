"""Движок Tavily. Импорт регистрирует его в реестрах поиска и получения контента."""

from src.modules.web_search.providers.registry import fetch_engines, search_engines
from src.modules.web_search.providers.tavily.client import TavilyEngine

_tavily = TavilyEngine()
search_engines.register(_tavily)
fetch_engines.register(_tavily)

__all__ = ["TavilyEngine"]
