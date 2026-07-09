"""Серверный audit-middleware MCP: пишет каждый вызов инструмента в ``mcp/audit``.

Форковский ``Middleware.on_call_tool`` оборачивает все инструменты всех
смонтированных серверов (один экземпляр на ``McpServerContext``). Лог-строка:
``principal · tool · сводка-аргументов · ok/err · ms``. Принципала читаем из
auth-контекста (``get_access_token().client_id`` = ``user.id``); при in-memory
``Client`` (тесты, без транспорта/auth) токена нет → ``-``.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware

from src.core.loggers import get_logger

if TYPE_CHECKING:
    from fastmcp.server.middleware import CallNext, MiddlewareContext
    from fastmcp.tools.tool import ToolResult

_LOG = get_logger("mcp/audit")
_ARGS_MAX = 200  # обрезка сводки аргументов, чтобы не раздувать лог


def _summarize(arguments: Any) -> str:
    s = repr(arguments)
    return s if len(s) <= _ARGS_MAX else s[:_ARGS_MAX] + "…"


class McpServerAuditMiddleware(Middleware):
    """Логирует исход каждого ``call_tool`` в канал ``mcp/audit``."""

    async def on_call_tool(
        self,
        context: "MiddlewareContext",
        call_next: "CallNext",
    ) -> "ToolResult":
        token = get_access_token()
        principal = token.client_id if token is not None else "-"
        name = context.message.name
        args = _summarize(context.message.arguments)
        start = time.monotonic()
        try:
            result = await call_next(context)
        except Exception as exc:  # noqa: BLE001 — пробрасываем после лога
            ms = (time.monotonic() - start) * 1000
            _LOG.info(
                "mcp user=%s tool=%s args=%s err=%r %.0fms",
                principal, name, args, exc, ms,
            )
            raise
        ms = (time.monotonic() - start) * 1000
        _LOG.info(
            "mcp user=%s tool=%s args=%s ok %.0fms", principal, name, args, ms
        )
        return result


__all__ = ["McpServerAuditMiddleware"]
