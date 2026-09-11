"""Коннектор Firecrawl: тонкий клиент к API + модели параметров запросов."""

from src.modules.core_connectors.connectors.firecrawl.connector import FirecrawlConnector
from src.modules.core_connectors.connectors.firecrawl.params import (
    FirecrawlCrawlParams,
    FirecrawlMapParams,
    FirecrawlScrapeOptions,
    FirecrawlScrapeParams,
    FirecrawlSearchParams,
)

__all__ = [
    "FirecrawlConnector",
    "FirecrawlScrapeOptions",
    "FirecrawlScrapeParams",
    "FirecrawlSearchParams",
    "FirecrawlMapParams",
    "FirecrawlCrawlParams",
]
