"""Runtime-настройки web_search (таблица core_modules_settings).

Модуль различает две функции внешнего веба, у каждой свой выбор:
- ``search_engine`` — движок поиска (Tavily / Firecrawl / Grok), отдаёт ссылки;
- получение контента страниц (Tavily / Firecrawl / simple-web-scraper; Grok не умеет) —
  основной маршрут ``fetch_engine``, запасной ``fetch_engine_fallback`` и зоны доменов
  каждого (``fetch_engine_zones`` / ``fetch_engine_fallback_zones``). Маршрут — движок вместе
  с подключением; варианты собираются из подключений в момент показа
  (``services/fetch_routes.py``), поэтому второй экземпляр скрейпера виден здесь сразу.

Токены движков тут НЕ живут — они в записях доступа модуля ``core_connectors``; адаптеры
web_search получают готовый коннектор через ``core_connectors.service.open_connector``.
Привязка потребителя к сервису — это код движка (``tavily``), он же код коннектора. Всё
читается через ``get_module_store("web_search")``.
"""

from __future__ import annotations

from src.core.settings import ChoiceField, IntField, ListField, StrField, get_module_store
from src.modules.web_search.services.fetch_routes import (
    NO_FALLBACK,
    fallback_route_options,
    route_options,
)

SEARCH_ENGINE_DEFAULT = "tavily"
FETCH_ENGINE_DEFAULT = "tavily"
FETCH_CONCURRENCY_DEFAULT = 5
DEFAULT_PAGES_DEFAULT = 10
MAX_CONCURRENT_SEARCHES_DEFAULT = 3

_SEARCH = "Поиск"
_FETCH = "Скачивание страниц"
_ZONES = "Доменные зоны"
_LIMITS = "Ограничения"

# Зона — домен или его хвост (``example.com``, ``.ru``, ``.рф``); пустая строка игнорируется.
_ZONE = StrField(key="zone", label="Зона", max_length=253, pattern=r"[^\s/:@]*")

SCHEMA = (
    ChoiceField(
        key="search_engine",
        label="Поисковый движок",
        description="Находит ссылки по запросу. Сами страницы скачивает основной движок.",
        default_=SEARCH_ENGINE_DEFAULT,
        options=(("tavily", "Tavily"), ("firecrawl", "Firecrawl"), ("xai", "Grok (xAI)")),
        group=_SEARCH,
    ),
    ChoiceField(
        key="fetch_engine",
        label="Основной движок",
        description="Скачивает найденные страницы.",
        default_=FETCH_ENGINE_DEFAULT,
        options_provider=route_options,
        group=_FETCH,
    ),
    ChoiceField(
        key="fetch_engine_fallback",
        label="Запасной движок",
        description=(
            "Скачивает то, что не скачал основной: заблокированные, недоступные и пустые "
            "страницы. Страницы, которых нет (404), не повторяет."
        ),
        default_=NO_FALLBACK,
        options_provider=fallback_route_options,
        group=_FETCH,
    ),
    ListField(
        key="fetch_engine_zones",
        label="Только через основной движок",
        description=(
            "Если основной не скачал страницу, в запасной она не уходит. "
            "Например: example.com с поддоменами, .org."
        ),
        item=_ZONE,
        group=_ZONES,
    ),
    ListField(
        key="fetch_engine_fallback_zones",
        label="Только через запасной движок",
        description=(
            "Эти домены основной движок не трогает. Если запасной не выбран, список не "
            "действует. Например: .ru, .рф, .su."
        ),
        item=_ZONE,
        group=_ZONES,
    ),
    IntField(
        key="default_pages",
        label="Страниц на поисковый запрос",
        description="Сколько ссылок брать из выдачи, если запрос не задаёт своё число.",
        default_=DEFAULT_PAGES_DEFAULT,
        min=1,
        max=50,
        group=_LIMITS,
    ),
    IntField(
        key="max_concurrent_searches",
        label="Поисков одновременно",
        description=(
            "Для каждого поискового движка. Сверх этого числа поиск ждёт своей очереди, "
            "а не падает с ошибкой."
        ),
        default_=MAX_CONCURRENT_SEARCHES_DEFAULT,
        min=1,
        max=50,
        group=_LIMITS,
    ),
    IntField(
        key="fetch_concurrency",
        label="Запросов на скачивание одновременно",
        description="Для каждого поиска. Сколько страниц входит в один запрос, зависит от движка.",
        default_=FETCH_CONCURRENCY_DEFAULT,
        min=1,
        max=50,
        group=_LIMITS,
    ),
)


def _setting(field_key: str, fallback):
    """Настройка из store; ``fallback``, если store ещё не загружен (скрипт/тест)."""
    try:
        return getattr(get_module_store("web_search"), field_key)
    except RuntimeError:
        return fallback


def search_engine() -> str:
    """Активный движок поиска."""
    return _setting("search_engine", SEARCH_ENGINE_DEFAULT)


def fetch_engine() -> str:
    """Код основного маршрута получения контента."""
    return _setting("fetch_engine", FETCH_ENGINE_DEFAULT)


def fetch_engine_fallback() -> str:
    """Код запасного маршрута; пусто — запасного нет."""
    return _setting("fetch_engine_fallback", NO_FALLBACK)


def fetch_engine_zones() -> list[str]:
    """Зоны доменов, которые идут только через основной маршрут."""
    return _setting("fetch_engine_zones", [])


def fetch_engine_fallback_zones() -> list[str]:
    """Зоны доменов, которые сразу идут через запасной маршрут."""
    return _setting("fetch_engine_fallback_zones", [])


def default_pages() -> int:
    """Сколько результатов (страниц) тянуть на поиск по умолчанию."""
    return _setting("default_pages", DEFAULT_PAGES_DEFAULT)


def max_concurrent_searches() -> int:
    """Потолок одновременных поисков на движок (сверх — задержка, не ошибка)."""
    return _setting("max_concurrent_searches", MAX_CONCURRENT_SEARCHES_DEFAULT)


def fetch_concurrency() -> int:
    """Лимит одновременных получений контента страниц внутри одного поиска."""
    return _setting("fetch_concurrency", FETCH_CONCURRENCY_DEFAULT)


__all__ = [
    "SCHEMA",
    "search_engine",
    "fetch_engine",
    "fetch_engine_fallback",
    "fetch_engine_zones",
    "fetch_engine_fallback_zones",
    "default_pages",
    "max_concurrent_searches",
    "fetch_concurrency",
]
