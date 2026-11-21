"""Коннектор simple-web-scraper: тонкий клиент к демону + модели параметров запросов."""

from src.modules.core_connectors.connectors.simple_web_scraper.connector import (
    SimpleWebScraperConnector,
)
from src.modules.core_connectors.connectors.simple_web_scraper.params import (
    SimpleWebScraperScrapBatchParams,
)

__all__ = [
    "SimpleWebScraperConnector",
    "SimpleWebScraperScrapBatchParams",
]
