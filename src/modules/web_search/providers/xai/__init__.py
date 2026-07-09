"""Провайдер Grok (xAI). Импорт регистрирует его как движок поиска (контент не умеет)."""

from src.modules.web_search.providers.registry import search_engines
from src.modules.web_search.providers.xai.client import XaiSearchEngine

search_engines.register(XaiSearchEngine())

__all__ = ["XaiSearchEngine"]
