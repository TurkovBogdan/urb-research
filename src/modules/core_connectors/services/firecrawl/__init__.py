"""Коннектор Firecrawl: тонкий клиент к API + модели параметров запросов."""

from src.modules.core_connectors.services.firecrawl.gateway import FirecrawlGateway
from src.modules.core_connectors.services.firecrawl.params import (
    FirecrawlCrawlParams,
    FirecrawlMapParams,
    FirecrawlScrapeOptions,
    FirecrawlScrapeParams,
    FirecrawlSearchParams,
)

__all__ = [
    "FirecrawlGateway",
    "FirecrawlScrapeOptions",
    "FirecrawlScrapeParams",
    "FirecrawlSearchParams",
    "FirecrawlMapParams",
    "FirecrawlCrawlParams",
]
