"""Runtime-настройки core_connectors: креды внешних сервисов (секреты).

Ключи хранятся в ``core_modules_settings`` под модулем ``core_connectors``, маскируются
на чтение и правятся на ``/core/settings``. Читаются через
``get_module_store("core_connectors")``. ENV не используется — ключи горячие,
переключаемые на лету (граница «ENV = только bootstrap до БД» сюда не попадает).
"""

from __future__ import annotations

from src.core.settings import BoolField, StrField, get_module_store

MODULE = "core_connectors"

SCHEMA = (
    BoolField(
        key="tavily_gateway_enabled",
        label="Включить Tavily",
        description="Сервис для поиска информации в вебе и извлечения контента страниц.",
        default_=True,
    ),
    StrField(
        key="tavily_api_key",
        label="API-ключ Tavily",
        description="Секретный ключ доступа к API Tavily. Получить: [app.tavily.com](https://app.tavily.com/home).",
        secret=True,
    ),
    BoolField(
        key="firecrawl_gateway_enabled",
        label="Включить Firecrawl",
        description="Сервис для скрапинга веб-страниц и поиска информации.",
        default_=True,
    ),
    StrField(
        key="firecrawl_api_key",
        label="API-ключ Firecrawl",
        description="Секретный ключ доступа к API Firecrawl. Получить: [firecrawl.dev](https://www.firecrawl.dev/app/api-keys).",
        secret=True,
    ),
    BoolField(
        key="xai_gateway_enabled",
        label="Включить Grok (xAI)",
        description="ИИ-модель Grok для агентского поиска в вебе и соцсети X.",
        default_=True,
    ),
    StrField(
        key="xai_api_key",
        label="API-ключ xAI",
        description="Секретный ключ доступа к API xAI. Получить: [console.x.ai](https://console.x.ai).",
        secret=True,
    ),
    StrField(
        key="xai_management_api_key",
        label="Management-ключ xAI",
        description="Секретный ключ Management API xAI — для баланса и лимитов трат. Отдельный от основного API-ключа. Создать: [console.x.ai](https://console.x.ai) → Settings → Management Keys.",
        secret=True,
    ),
    BoolField(
        key="openrouter_gateway_enabled",
        label="Включить OpenRouter",
        description="Единый API-шлюз к LLM разных провайдеров.",
        default_=True,
    ),
    StrField(
        key="openrouter_api_key",
        label="API-ключ OpenRouter",
        description="Секретный ключ доступа к API OpenRouter. Получить: [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys).",
        secret=True,
    ),
    BoolField(
        key="openai_gateway_enabled",
        label="Включить OpenAI",
        description="LLM-провайдер OpenAI (GPT, o-серия). Для расхода нужен Admin-ключ.",
        default_=True,
    ),
    StrField(
        key="openai_admin_api_key",
        label="Admin-ключ OpenAI",
        description="Секретный Admin-ключ OpenAI (sk-admin-…) — для отчёта о расходах. Обычный API-ключ не подойдёт. Создать: [platform.openai.com](https://platform.openai.com/settings/organization/admin-keys).",
        secret=True,
    ),
    BoolField(
        key="anthropic_gateway_enabled",
        label="Включить Anthropic (Claude)",
        description="LLM-провайдер Anthropic (Claude). Для расхода нужен Admin-ключ.",
        default_=True,
    ),
    StrField(
        key="anthropic_admin_api_key",
        label="Admin-ключ Anthropic",
        description="Секретный Admin-ключ Anthropic (sk-ant-admin…) — для отчёта о расходах. Обычный API-ключ не подойдёт. Создать: [console.anthropic.com](https://console.anthropic.com/settings/admin-keys).",
        secret=True,
    ),
    BoolField(
        key="web_scrapper_gateway_enabled",
        label="Включить daemon-web-scrapper",
        description="Локальный браузерный демон (порт 19020) для скрейпинга страниц в markdown.",
        default_=True,
    ),
    StrField(
        key="web_scrapper_api_key",
        label="Токен daemon-web-scrapper",
        description="Bearer-токен демона (SCRAPER_API_KEY). Оставьте пустым, если у демона авторизация отключена.",
        secret=True,
    ),
)


def service_api_key(field_key: str) -> str:
    """Токен сервиса из runtime-настроек; пусто, если не задан/store не загружен."""
    try:
        return getattr(get_module_store(MODULE), field_key)
    except RuntimeError:
        return ""


def service_enabled(field_key: str) -> bool:
    """Включён ли шлюз (runtime-настройка); True, если store ещё не загружен (скрипт/тест)."""
    try:
        return getattr(get_module_store(MODULE), field_key)
    except RuntimeError:
        return True


__all__ = ["SCHEMA", "MODULE", "service_api_key", "service_enabled"]
