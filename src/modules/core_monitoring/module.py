"""Module-провайдер модуля core_monitoring.

Инфра-модуль наблюдаемости: отдаёт раздел задач (список зарегистрированных
scheduler-задач + их запуски и логи). Своих таблиц/миграций/настроек нет —
читает core-CRUD (`core/crud/tasks`, `tasks_logs`) и реестр планировщика.
"""

from __future__ import annotations

from typing import ClassVar

from fastapi import FastAPI

from src.core.config import Config
from src.core.loggers import get_logger
from src.core.loggers.logger_protocol import CoreLoggerProtocol
from src.core.module import Module
from src.modules.core_monitoring.api import internal_router
from src.modules.core_monitoring.constants import LOG_CHANNEL


class CoreMonitoringModule(Module):
    name: ClassVar[str] = "core_monitoring"
    description: ClassVar[str] = "Наблюдаемость планировщика: список задач, их запуски и логи."
    migrations_dir = None
    config_cls = None
    settings_schema = None
    internal_router = internal_router
    internal_router_prefix = ""

    @staticmethod
    def logger() -> CoreLoggerProtocol:
        return get_logger(LOG_CHANNEL)

    def configure(self, app: FastAPI, config: Config) -> None:
        pass


__all__ = ["CoreMonitoringModule"]
