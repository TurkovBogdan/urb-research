"""Адаптер Grok (xAI) как движок поиска поверх коннектора ``core_connectors``.

У xAI нет отдельного search-эндпойнта: «поиск» — это инференс ``responses()`` с
server-side инструментом ``web_search`` + строгий structured output. Модель сама
ранжирует найденное и возвращает JSON-массив ``links`` (url/title/summary/reason/relevance,
схема ``LINKS_SCHEMA``, strict) — это даёт релевантность, краткое содержание и обоснование,
которых нет в сырых цитатах. Но URL печатает **сама модель**, поэтому оставляем только те
ссылки, что реально посещены поиском: сверяем ``links[].url`` с ``web_search_call.action.sources``
(по нормализованному url) и отбрасываем невстреченные (защита от галлюцинированных URL).
Контент Grok здесь не отдаёт — это **только** движок поиска (роль ``SearchEngine``).
Домены: ``include_domains`` → ``allowed_domains`` (≤5), иначе ``exclude_domains`` →
``excluded_domains``; ``time_range`` xAI web_search не поддерживает — опускаем.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from src.modules.core_connectors.services.xai import (
    GROK_FLAGSHIP,
    XaiGateway,
    XaiResponsesParams,
    XaiWebSearchFilters,
    XaiWebSearchTool,
    json_schema_text,
)
from src.modules.web_search.providers.base import SearchEngine
from src.modules.web_search.providers.request import SearchRequest

_MAX_DOMAIN_FILTERS = 5

AGENT_INSTRUCTION = (
    "Ты ассистент-ресёрчер. По запросу пользователя найди в вебе самые релевантные "
    "источники (официальная документация, авторитетные статьи, разборы). Верни только "
    "ссылки, отсортированные по убыванию релевантности; не выдумывай URL — бери из поиска. "
    "Для каждой ссылки укажи summary — краткое содержание страницы (2–3 предложения) в "
    "контексте запроса, и reason — почему она релевантна."
)

LINKS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "reason": {"type": "string"},
                    "relevance": {"type": "number"},
                },
                "required": ["url", "title", "summary", "reason", "relevance"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["links"],
    "additionalProperties": False,
}


class XaiSearchEngine(SearchEngine):
    code: ClassVar[str] = "xai"
    enabled_field: ClassVar[str] = XaiGateway.ENABLED_FIELD

    def __init__(self) -> None:
        self.gateway = XaiGateway()

    async def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        tool = XaiWebSearchTool(filters=_domain_filters(request))
        params = XaiResponsesParams(
            model=GROK_FLAGSHIP,
            instructions=AGENT_INSTRUCTION,
            input=request.query,
            tools=[tool],
            text=json_schema_text("relevant_links", LINKS_SCHEMA),
        )
        data = await self.gateway.responses(params)
        grounded = _grounded_links(_parsed_links(data), _searched_urls(data))
        return [
            {
                "url": link["url"],
                "rank": rank,
                "score": link.get("relevance"),
                "summary": link.get("summary"),
                "title": link.get("title"),
                "meta": {"reason": link.get("reason")},
            }
            for rank, link in enumerate(grounded[: request.max_results], 1)
        ]


def _domain_filters(request: SearchRequest) -> XaiWebSearchFilters | None:
    """``allowed_domains`` (по include) ИЛИ ``excluded_domains`` (по exclude); xAI не даёт оба."""
    if request.include_domains:
        return XaiWebSearchFilters(
            allowed_domains=list(request.include_domains)[:_MAX_DOMAIN_FILTERS]
        )
    if request.exclude_domains:
        return XaiWebSearchFilters(
            excluded_domains=list(request.exclude_domains)[:_MAX_DOMAIN_FILTERS]
        )
    return None


def _norm_url(url: str | None) -> str:
    return (url or "").rstrip("/").lower()


def _parsed_links(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Строгий JSON финального message → его массив ``links`` (пустой при сбое разбора)."""
    for item in reversed(data.get("output") or []):
        if item.get("type") != "message":
            continue
        for block in item.get("content") or []:
            text = block.get("text")
            if not text:
                continue
            try:
                return json.loads(text).get("links") or []
            except (json.JSONDecodeError, AttributeError):
                return []
    return []


def _searched_urls(data: dict[str, Any]) -> set[str]:
    """Нормализованные URL, реально посещённые поиском (``web_search_call.action.sources``)."""
    searched: set[str] = set()
    for item in data.get("output") or []:
        if item.get("type") != "web_search_call":
            continue
        for source in (item.get("action") or {}).get("sources") or []:
            url = source if isinstance(source, str) else source.get("url")
            searched.add(_norm_url(url))
    return searched


def _grounded_links(
    links: list[dict[str, Any]], searched: set[str]
) -> list[dict[str, Any]]:
    """Оставить только ссылки, встреченные реальным поиском (порядок модели сохраняем)."""
    return [link for link in links if _norm_url(link.get("url")) in searched]


__all__ = ["XaiSearchEngine"]
