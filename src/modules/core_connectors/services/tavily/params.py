"""Модели параметров запросов Tavily — по модели на метод (search/extract/map/crawl).

Каждая модель = типизированный набор полей запроса; ``to_payload()`` даёт JSON-тело,
опуская незаданные (``None``) поля — дефолты применяет сам Tavily, шлюз их не
навязывает. Формы соответствуют докам docs.tavily.com. Только параметры запроса;
ответ шлюз отдаёт нативным (маппинг под домен — на стороне потребителя).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class _TavilyParams(BaseModel):
    def to_payload(self) -> dict[str, Any]:
        """JSON-тело запроса: только явно заданные поля (``None`` опускаются)."""
        return self.model_dump(exclude_none=True)


class TavilySearchParams(_TavilyParams):
    """Поиск Tavily (``/search``). Поле ``include_raw_content`` намеренно НЕ проброшено:
    поиск отдаёт только ссылки, тело страниц тянет отдельная стадия (``/extract``) — единый
    двухстадийный контракт для всех провайдеров web_search (Tavily не «особый»)."""

    query: str
    search_depth: str | None = None  # ultra-fast | fast | basic | advanced
    chunks_per_source: int | None = None  # 1–3, только для advanced
    max_results: int | None = None  # 0–20
    topic: str | None = None  # general | news | finance
    time_range: str | None = None  # day/week/month/year (или d/w/m/y)
    start_date: str | None = None  # YYYY-MM-DD
    end_date: str | None = None  # YYYY-MM-DD
    include_answer: bool | str | None = None  # true | basic | advanced
    include_images: bool | None = None
    include_image_descriptions: bool | None = None
    include_favicon: bool | None = None
    include_domains: list[str] | None = None  # до 300
    exclude_domains: list[str] | None = None  # до 150
    country: str | None = None  # полное имя страны, только topic=general
    auto_parameters: bool | None = None
    exact_match: bool | None = None
    include_usage: bool | None = None
    safe_search: bool | None = None  # Enterprise


class TavilyExtractParams(_TavilyParams):
    urls: list[str]
    query: str | None = None  # интент для реранжирования извлечённых чанков
    chunks_per_source: int | None = None  # 1–5
    extract_depth: str | None = None  # basic | advanced
    format: str | None = None  # markdown | text
    include_images: bool | None = None
    include_favicon: bool | None = None
    timeout: float | None = None  # 1.0–60.0
    include_usage: bool | None = None


class _TavilyTraversalParams(_TavilyParams):
    """Общие поля обхода дерева ссылок — у ``/map`` и ``/crawl`` (регэксп-фильтры)."""

    url: str
    instructions: str | None = None  # NL-инструкции обхода (2 кр/10 стр вместо 1)
    max_depth: int | None = None  # 1–5, как далеко от корня
    max_breadth: int | None = None  # 1–500, ссылок на уровень
    limit: int | None = None  # всего ссылок до остановки
    select_paths: list[str] | None = None  # регэкспы путей — только совпадающие
    select_domains: list[str] | None = None
    exclude_paths: list[str] | None = None
    exclude_domains: list[str] | None = None
    allow_external: bool | None = None  # включать ссылки на внешние домены
    timeout: float | None = None  # 10–150
    include_usage: bool | None = None


class TavilyMapParams(_TavilyTraversalParams):
    """Карта ссылок сайта (``/map``): только обход, без контента."""


class TavilyCrawlParams(_TavilyTraversalParams):
    """Обход сайта с контентом (``/crawl``): обход + извлечение тела страниц."""

    chunks_per_source: int | None = None  # 1–5
    extract_depth: str | None = None  # basic | advanced
    format: str | None = None  # markdown | text
    include_images: bool | None = None
    include_favicon: bool | None = None


__all__ = [
    "TavilySearchParams",
    "TavilyExtractParams",
    "TavilyMapParams",
    "TavilyCrawlParams",
]
