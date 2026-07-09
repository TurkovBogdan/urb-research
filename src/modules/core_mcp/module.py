"""Module-провайдер модуля core_mcp.

Инфра-модуль интроспекции MCP-серверов: прикладная поверхность над фундаментом
``src/core/mcp/`` (тот правит контракт ``Module`` и монтирует сабапы — модулем
быть не может). Здесь — только чтение: API ``/core-mcp/servers`` отдаёт список
поднятых серверов, их инструменты и конфиг подключения для UI. Своих таблиц/
миграций/настроек нет; читает живые инстансы из ``app.state.mcp_servers``.
"""

from __future__ import annotations

from typing import ClassVar

from fastapi import FastAPI

from src.core.config import Config
from src.core.module import Module
from src.modules.core_mcp.api import router as mcp_router


class CoreMcpModule(Module):
    name: ClassVar[str] = "core_mcp"
    description: ClassVar[str] = "Интроспекция поднятых MCP-серверов: их инструменты и конфиг подключения."
    migrations_dir = None
    config_cls = None
    settings_schema = None
    internal_router = mcp_router
    internal_router_prefix = "/core-mcp"

    def configure(self, app: FastAPI, config: Config) -> None:
        pass


__all__ = ["CoreMcpModule"]
