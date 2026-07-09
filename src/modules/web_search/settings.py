"""Runtime-настройки web_search (таблица core_modules_settings).

Модуль различает две функции внешнего веба, у каждой свой движок по умолчанию:
- ``search_engine`` — движок поиска (Tavily / Firecrawl / Grok), отдаёт ссылки;
- ``fetch_engine`` — движок получения контента страниц (Tavily / Firecrawl / daemon-web-scrapper; Grok не умеет).

Токены движков тут НЕ живут — они в модуле ``core_connectors`` (коннекторы владеют кредами);
адаптеры web_search берут ключ через ``core_connectors.settings.service_api_key``. Всё
читается через ``get_module_store("web_search")``.
"""

from __future__ import annotations

from src.core.settings import ChoiceField, IntField, get_module_store

SEARCH_ENGINE_DEFAULT = "tavily"
FETCH_ENGINE_DEFAULT = "tavily"
FETCH_CONCURRENCY_DEFAULT = 5
DEFAULT_PAGES_DEFAULT = 10
MAX_CONCURRENT_SEARCHES_DEFAULT = 3

SCHEMA = (
    ChoiceField(
        key="search_engine",
        label="Поисковый движок",
        description="Движок, который по запросу возвращает ссылки.",
        default_=SEARCH_ENGINE_DEFAULT,
        options=(("tavily", "Tavily"), ("firecrawl", "Firecrawl"), ("xai", "Grok (xAI)")),
    ),
    ChoiceField(
        key="fetch_engine",
        label="Сервис получения контента",
        description="Что использовать для получения контента страниц",
        default_=FETCH_ENGINE_DEFAULT,
        options=(
            ("tavily", "Tavily"),
            ("firecrawl", "Firecrawl"),
            ("web_scrapper", "daemon-web-scrapper"),
        ),
    ),
    IntField(
        key="default_pages",
        label="Страниц на поисковый запрос",
        description="Сколько результатов (страниц) тянуть на один поисковый запрос, если не задано явно.",
        default_=DEFAULT_PAGES_DEFAULT,
        min=1,
        max=50,
    ),
    IntField(
        key="max_concurrent_searches",
        label="Максимум параллельных поисковых запросов",
        description=(
            "Сколько поисков одного движка может идти одновременно; сверх лимита новый "
            "поиск ждёт освобождения слота (задержка, не ошибка). Фетч ограничивается заодно."
        ),
        default_=MAX_CONCURRENT_SEARCHES_DEFAULT,
        min=1,
        max=50,
    ),
    IntField(
        key="fetch_concurrency",
        label="Максимум параллельных запросов получения контента",
        description="Сколько страниц скрапится одновременно внутри одного поиска.",
        default_=FETCH_CONCURRENCY_DEFAULT,
        min=1,
        max=50,
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
    """Активный движок получения контента."""
    return _setting("fetch_engine", FETCH_ENGINE_DEFAULT)


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
    "default_pages",
    "max_concurrent_searches",
    "fetch_concurrency",
]
