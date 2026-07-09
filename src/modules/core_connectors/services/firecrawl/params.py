"""Модели параметров запросов Firecrawl — по модели на метод (scrape/search/map/crawl).

Firecrawl принимает поля в camelCase; модели держат pythonic snake_case + генератор
алиасов ``to_camel``, а ``to_payload()`` дампит ``by_alias`` (→ camelCase), опуская
незаданные (``None``) поля — дефолты применяет сам Firecrawl. Формы по докам
docs.firecrawl.dev. ``FirecrawlScrapeOptions`` = поля скрейпа без ``url``, переиспользуются
как вложенный ``scrape_options`` в search/crawl (``FirecrawlScrapeParams`` = options + url).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _FirecrawlParams(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def to_payload(self) -> dict[str, Any]:
        """JSON-тело запроса (camelCase): только явно заданные поля (``None`` опускаются)."""
        return self.model_dump(by_alias=True, exclude_none=True)


class FirecrawlScrapeOptions(_FirecrawlParams):
    formats: list[str] | None = None  # markdown | html | rawHtml | links | screenshot | json | summary
    only_main_content: bool | None = None  # readability: режет меню/шапку/футер
    include_tags: list[str] | None = None
    exclude_tags: list[str] | None = None
    max_age: int | None = None  # мс: отдать кэш, если моложе
    wait_for: int | None = None  # мс: пауза перед снятием (ждём JS)
    timeout: int | None = None  # мс: 1000–300000
    mobile: bool | None = None
    parsers: list[Any] | None = None  # обработка файлов (напр. pdf)
    actions: list[dict[str, Any]] | None = None  # click/type/scroll/wait
    location: dict[str, Any] | None = None  # {country, languages}
    block_ads: bool | None = None
    proxy: str | None = None  # basic | enhanced | auto
    remove_base64_images: bool | None = None
    store_in_cache: bool | None = None


class FirecrawlScrapeParams(FirecrawlScrapeOptions):
    url: str


class FirecrawlSearchParams(_FirecrawlParams):
    query: str  # ≤500 символов
    limit: int | None = None  # 1–100 (на источник)
    sources: list[str] | None = None  # web | news | images
    categories: list[str] | None = None  # github | research | pdf
    tbs: str | None = None  # qdr:d/w/m/y или диапазон дат
    location: str | None = None  # гео, напр. "Germany"
    timeout: int | None = None  # мс: 1000–300000
    ignore_invalid_urls: bool | None = None
    scrape_options: FirecrawlScrapeOptions | None = None  # контент инлайн


class FirecrawlMapParams(_FirecrawlParams):
    url: str
    search: str | None = None  # ранжировать результаты по релевантности запросу
    sitemap: str | None = None  # skip | include | only
    include_subdomains: bool | None = None
    ignore_query_parameters: bool | None = None
    ignore_cache: bool | None = None
    limit: int | None = None  # до 100000
    timeout: int | None = None  # мс
    location: dict[str, Any] | None = None


class FirecrawlCrawlParams(_FirecrawlParams):
    url: str
    prompt: str | None = None  # NL-промпт → опции обхода
    include_paths: list[str] | None = None  # регэкспы путей
    exclude_paths: list[str] | None = None
    max_discovery_depth: int | None = None
    sitemap: str | None = None  # skip | include | only
    ignore_query_parameters: bool | None = None
    regex_on_full_url: bool | None = None
    limit: int | None = None  # до 10000
    crawl_entire_domain: bool | None = None
    allow_external_links: bool | None = None
    allow_subdomains: bool | None = None
    delay: float | None = None  # сек между скрейпами
    max_concurrency: int | None = None
    scrape_options: FirecrawlScrapeOptions | None = None


__all__ = [
    "FirecrawlScrapeOptions",
    "FirecrawlScrapeParams",
    "FirecrawlSearchParams",
    "FirecrawlMapParams",
    "FirecrawlCrawlParams",
]
