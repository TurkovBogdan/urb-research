"""Модуль ``core_connectors`` — коннекторы к внешним API + хранение их кредов.

Инфраструктурный (``core_*``) модуль без домена: держит runtime-настройки с
токенами сервисов (Tavily, Firecrawl) и тонкие коннекторы в ``services/``. Отдаёт
internal-эндпойнт ``/connectors`` (паспорт + баланс) для раздела мониторинга. Своих
таблиц/миграций/задач нет.
"""

from __future__ import annotations

from typing import ClassVar

from src.core.module import Module
from src.modules.core_connectors.api import internal_router
from src.modules.core_connectors.settings import SCHEMA


class CoreConnectorsModule(Module):
    name: ClassVar[str] = "core_connectors"
    description: ClassVar[str] = "Коннекторы к внешним API (Tavily, Firecrawl) и хранение их токенов."
    settings_schema = SCHEMA
    internal_router = internal_router
    internal_router_prefix = ""


__all__ = ["CoreConnectorsModule"]
