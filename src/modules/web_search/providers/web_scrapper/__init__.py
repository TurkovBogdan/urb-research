"""Движок daemon-web-scrapper. Импорт регистрирует его в реестре получения контента (только фетч)."""

from src.modules.web_search.providers.registry import fetch_engines
from src.modules.web_search.providers.web_scrapper.client import WebScrapperEngine

_web_scrapper = WebScrapperEngine()
fetch_engines.register(_web_scrapper)

__all__ = ["WebScrapperEngine"]
