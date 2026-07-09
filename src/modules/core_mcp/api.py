"""Раздел «MCP-серверы» — интроспекция модулей, поднятых как MCP-серверы.

Поверхность только на чтение: перечисляет смонтированные ядром MCP-серверы
(``/mcp/<code>``) и отдаёт по каждому имя/версию/инструкции, список инструментов
и готовый stdio-конфиг для вставки в MCP-клиент. Источник истины — живые
``FastMCP``-инстансы, которые ``mount_mcp_servers`` кладёт в ``app.state.mcp_servers``
при сборке сервера; читаем их duck-typed (``name``/``version``/``instructions``/
``list_tools``), поэтому модуль НЕ импортирует ``fastmcp`` (воркер чист).

Корень ``/servers`` прописан в путях; зона навешивает префикс ``/core-mcp``.
Зона internal в чистом ядре = ``allow_all`` — guard не нужен.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.core.api import ApiError

# Корень проекта (…/src/modules/core_mcp/api.py → четыре уровня вверх) — идёт в
# `uv run --directory`, чтобы клиент со своим cwd всё равно попал в проект.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class McpToolInfo(BaseModel):
    name: str
    description: str | None
    input_schema: dict | None
    output_schema: dict | None


class McpServerSummary(BaseModel):
    code: str
    name: str
    version: str | None
    instructions: str | None
    tool_count: int


class McpServerDetail(BaseModel):
    code: str
    name: str
    version: str | None
    instructions: str | None
    tools: list[McpToolInfo]
    # Готовый JSON-конфиг подключения строкой, для копирования. Единый для Claude
    # Desktop и Claude Code — оба спавнят локальную stdio-обёртку `app.py --mcp-stdio`
    # (лёгкий демон-враппер), которая сама поднимает backend и мостит вызовы.
    connection_config: str


router = APIRouter()


def _servers(request: Request) -> dict[str, Any]:
    """Реестр живых MCP-инстансов из ``app.state`` (пусто, если зона не монтирована)."""
    return getattr(request.app.state, "mcp_servers", {})


async def _tools(mcp: Any) -> list[McpToolInfo]:
    """Инструменты сервера через интроспекцию (без middleware/auth — чистый список)."""
    return [
        McpToolInfo(
            name=t.name,
            description=t.description,
            input_schema=t.parameters,
            output_schema=t.output_schema,
        )
        for t in await mcp.list_tools(run_middleware=False)
    ]


def _uv_binary() -> str:
    """Абсолютный путь к ``uv`` для конфига (fallback — голое имя).

    MCP-клиенты часто стартуют с урезанным PATH, поэтому абсолютный путь надёжнее
    голого ``uv`` (иначе клиент не найдёт бинарь → «Connection Failed»).
    """
    return shutil.which("uv") or "uv"


def _stdio_config(code: str, pin_code: bool, token: str) -> str:
    """Конфиг подключения через stdio-обёртку (``app.py --mcp-stdio``).

    Клиент сам спавнит лёгкий демон-враппер по stdio — тот лениво поднимает backend и
    мостит вызовы инструментов на ``/mcp/<code>``. Вид единый для Claude Desktop и Claude
    Code. ``uv run --directory <root>`` фиксирует проект независимо от cwd клиента.
    ``MCP_STDIO_CODE`` пинуется только когда серверов несколько (иначе обёртка сама берёт
    единственный смонтированный). ``MCP_TOKEN`` (bearer MCP-серверов) кладём в env, если
    он задан — так подключение самодостаточно, не полагается на ``.env`` проекта.
    """
    server: dict[str, Any] = {
        "command": _uv_binary(),
        "args": [
            "run",
            "--directory",
            str(_PROJECT_ROOT),
            "python",
            "src/app.py",
            "--mcp-stdio",
        ],
    }
    env = {}
    if token:
        env["MCP_TOKEN"] = token
    if pin_code:
        env["MCP_STDIO_CODE"] = code
    if env:
        server["env"] = env
    return json.dumps({"mcpServers": {code: server}}, indent=2, ensure_ascii=False)


@router.get("/servers", response_model=list[McpServerSummary])
async def list_servers(request: Request) -> list[McpServerSummary]:
    """Сводка по всем смонтированным MCP-серверам (имя/версия/число инструментов)."""
    out: list[McpServerSummary] = []
    for code, mcp in _servers(request).items():
        out.append(
            McpServerSummary(
                code=code,
                name=mcp.name,
                version=mcp.version,
                instructions=mcp.instructions,
                tool_count=len(await mcp.list_tools(run_middleware=False)),
            )
        )
    out.sort(key=lambda s: s.code)
    return out


@router.get("/servers/{code}", response_model=McpServerDetail)
async def get_server(code: str, request: Request) -> McpServerDetail:
    """Детали одного сервера: инструкции, инструменты и конфиг подключения."""
    servers = _servers(request)
    mcp = servers.get(code)
    if mcp is None:
        raise ApiError.not_found(f"MCP-сервер {code!r} не найден")
    return McpServerDetail(
        code=code,
        name=mcp.name,
        version=mcp.version,
        instructions=mcp.instructions,
        tools=await _tools(mcp),
        connection_config=_stdio_config(
            code,
            pin_code=len(servers) > 1,
            token=request.app.state.config.mcp_token,
        ),
    )


__all__ = ["router"]
