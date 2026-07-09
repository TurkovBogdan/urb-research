"""Модуль ``web_search`` — поиск в вебе + сохранение найденных страниц.

Зона ответственности — поиск в вебе через движки (Tavily, Firecrawl, …) и сохранение
контента найденных страниц (markdown, дедуп по url). Тройка таблиц:
``web_search_query`` (прогоны поиска) → ``web_search_query_result`` (результаты запроса)
→ ``web_search_page`` (контент страницы, дедуп по url). Схема — миграции ``wsm_001..003``
(портируемые типы, идут и на SQLite, и на PG). Исполнение синхронное (``services/searcher.search``) —
ни очереди, ни планировщик-задач, ни ретраев. Активный провайдер — runtime-настройка
(``settings_schema``, правится на ``/core/settings``); токены провайдеров живут в
``core_connectors``.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from src.core.module import Module
from src.modules.web_search import models  # noqa: F401 — регистрирует модели в Base.metadata
from src.modules.web_search.api import router
from src.modules.web_search.settings import SCHEMA

_HERE = Path(__file__).resolve().parent


class WebSearchModule(Module):
    name: ClassVar[str] = "web_search"
    description: ClassVar[str] = "Поиск в вебе и сохранение найденных страниц в markdown."
    settings_schema = SCHEMA
    migrations_dir = _HERE / "migrations" / "versions"
    internal_router = router
    internal_router_prefix = "/web-search"


__all__ = ["WebSearchModule"]
