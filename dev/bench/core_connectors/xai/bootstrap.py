"""Поднять dev-БД + module store core_connectors для живых прогонов коннектора.

Ключи сервисов лежат в runtime-настройках (`core_modules_settings`, dev-sqlite), поэтому
коннектор видит их только после загрузки store. Здесь: init_database → register schema →
load_initial. Только чтение настроек, без DDL/деструктива. Вызывать перед XaiGateway().
"""

from __future__ import annotations

from src.core.settings.bootstrap import load_initial_stores, register_settings_schemas
from src.core.config import Config
from src.core.database import init_database
from src.modules.core_connectors import CoreConnectorsModule


async def load_gateway_store() -> None:
    await init_database(Config())
    modules = [CoreConnectorsModule()]
    register_settings_schemas(modules)
    await load_initial_stores(modules)
