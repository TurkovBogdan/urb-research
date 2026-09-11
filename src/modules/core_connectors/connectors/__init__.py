"""Коннекторы: что бывает в этой установке — по папке на внешний сервис.

Реестр держит классы. Встроенные вносятся при импорте этого пакета: они принадлежат
самому модулю, и их состав не зависит ни от сборки приложения, ни от базы — так реестр
полон и в скрипте, и в тесте, а не только внутри поднятого приложения. Чужой модуль
регистрирует свои коннекторы своим ``configure()`` (или позже — реестр динамический).
Повторная регистрация той же пары (класс, владелец) — no-op, поэтому переимпорт и
пересборка приложения безопасны.
"""

from src.modules.core_connectors.connectors.base import Connector, HttpConnector
from src.modules.core_connectors.connectors.firecrawl import FirecrawlConnector
from src.modules.core_connectors.connectors.groups import (
    CONNECTOR_GROUPS,
    ConnectorGroup,
    groups,
)
from src.modules.core_connectors.connectors.openrouter import OpenRouterConnector
from src.modules.core_connectors.connectors.passport import (
    BalanceMetric,
    ConnectorBalance,
    ConnectorCheck,
    ConnectorPassport,
)
from src.modules.core_connectors.connectors.registry import (
    ConnectorsRegistry,
    connectors_registry,
)
from src.modules.core_connectors.connectors.tavily import TavilyConnector
from src.modules.core_connectors.connectors.web_scrapper import WebScrapperConnector
from src.modules.core_connectors.connectors.xai import XaiConnector

BUILTIN_CONNECTORS: tuple[type[Connector], ...] = (
    TavilyConnector,
    FirecrawlConnector,
    XaiConnector,
    OpenRouterConnector,
    WebScrapperConnector,
)


OWNER = "core_connectors"


def register_builtin_connectors(owner: str = OWNER) -> None:
    """Внести встроенные коннекторы в реестр от имени модуля-владельца (идемпотентно)."""
    for connector in BUILTIN_CONNECTORS:
        connectors_registry.register(connector, owner=owner)


register_builtin_connectors()


__all__ = [
    "Connector",
    "HttpConnector",
    "ConnectorPassport",
    "ConnectorBalance",
    "BalanceMetric",
    "ConnectorCheck",
    "ConnectorGroup",
    "CONNECTOR_GROUPS",
    "groups",
    "ConnectorsRegistry",
    "connectors_registry",
    "BUILTIN_CONNECTORS",
    "OWNER",
    "register_builtin_connectors",
    "TavilyConnector",
    "FirecrawlConnector",
    "XaiConnector",
    "OpenRouterConnector",
    "WebScrapperConnector",
]
