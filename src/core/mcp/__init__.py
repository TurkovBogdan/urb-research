"""MCP-server-инструментарий ядра — единственная граница импорта ``fastmcp``.

Подпакет изолирует +13 МБ форка в одно backend-only место (его тянет только
``mount_mcp_servers`` под ``server_enabled`` — не воркер, не ``build_modules``)
и даёт модулям одну точку импорта: ``from src.core.mcp import make_mcp_server``.

НЕ модуль: основа И ЕСТЬ сборщик — она правит контракт ``Module`` и монтирует
приложения модулей в ``create_app``; зарегистрированный модуль так не может.
"""

from __future__ import annotations

from src.core.mcp.auth import McpServerTokenVerifier
from src.core.mcp.audit import McpServerAuditMiddleware
from src.core.mcp.context import (
    McpPrincipal,
    McpServerBuilder,
    McpServerContext,
    TokenResolver,
)
from src.core.mcp.factory import make_mcp_server

__all__ = [
    "McpPrincipal",
    "McpServerAuditMiddleware",
    "McpServerBuilder",
    "McpServerContext",
    "McpServerTokenVerifier",
    "TokenResolver",
    "make_mcp_server",
]
