"""Движок simple-web-scraper. Импорт регистрирует его в реестре получения контента (только фетч)."""

from src.modules.web_search.providers.registry import fetch_engines
from src.modules.web_search.providers.simple_web_scraper.client import SimpleWebScraperEngine

_simple_web_scraper = SimpleWebScraperEngine()
fetch_engines.register(_simple_web_scraper)

__all__ = ["SimpleWebScraperEngine"]
