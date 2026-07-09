"""Состав модулей приложения ``apps/app``.

Единый источник списка модулей: его переиспользуют сборка приложения
(``server.py``) и standalone-применение миграций (``app.py migrate``), чтобы
``version_locations`` совпадали с тем, что реально поднимает сервер.
"""

from __future__ import annotations

from src.core.module import Module
from src.modules.core_connectors import CoreConnectorsModule
from src.modules.core_mcp import CoreMcpModule
from src.modules.core_monitoring import CoreMonitoringModule
from src.modules.core_setup import CoreSetupModule
from src.modules.research import ResearchModule
from src.modules.web_search import WebSearchModule


def build_modules() -> list[Module]:
    """Список модулей приложения в порядке регистрации.

    Поверх ядра (``src/core``: миграции, планировщик, зоны роутера, раздача SPA,
    settings-store) подключены ``core_setup`` — страница настроек ENV (правка ``.env``
    + рестарт), ``core_connectors`` — коннекторы к внешним API + хранение их кредов
    (runtime-настройки), ``core_monitoring`` — раздел задач (список + запуски + логи,
    только чтение), ``core_mcp`` — интроспекция модулей, поднятых как MCP-серверы
    (только чтение), ``web_search`` (поиск в вебе + сохранение найденных страниц:
    запросы/выдача/страницы) и ``research`` —
    оркестратор + реестр ресёрча (пока болванка). Новый модуль — добавить
    инстанс в список.
    """
    return [
        CoreSetupModule(),
        CoreConnectorsModule(),
        CoreMonitoringModule(),
        CoreMcpModule(),
        WebSearchModule(),
        ResearchModule(),
    ]


__all__ = ["build_modules"]
