"""Зона ``mcp`` — модули как MCP-серверы под ``/mcp/<code>``.

Не APIRouter-зона: каждый MCP-сервер — отдельное ASGI-подприложение (форк
``fastmcp``, Streamable HTTP), смонтированное на ``app.mount``. Граница монтажа
обходит FastAPI ``dependencies=[...]``, поэтому auth живёт ВНУТРИ сервера
(``McpServerTokenVerifier``), а не зон-guard'ом.

``mount_mcp_servers`` — зон-клей: собирает один ``McpServerContext`` (общий
verifier + audit + allowed_hosts), монтирует ``(code, mcp_server)`` всех модулей
и возвращает их lifespan-ы наверх в ``create_app`` (там они композируются —
без этого session manager форка не инициализируется → 500).

Импорт ``src.core.mcp`` (→ ``fastmcp``, +13 МБ) держим ВНУТРИ функции: модуль
тянет ``app_factory`` → ``mounting`` в любом процессе, а сам монтаж зовётся лишь
под ``server_enabled`` — так форк не попадает в воркер.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

from src.core.config import Config
from src.core.loggers import get_logger
from src.core.module import Module

if TYPE_CHECKING:
    from src.core.mcp import TokenResolver

_LOG = get_logger()

# Префикс монтажа зоны: ``/mcp/<code>`` на сервер.
MCP_PREFIX = "/mcp"


def _collect_resolver(modules: Sequence[Module]) -> "TokenResolver":
    """Единственный ``mcp_token_resolver`` с модулей (как ``build_guard_registry``).

    Его поставляет auth-модуль; несколько поставщиков → ошибка конфигурации.
    Вызывается только когда есть хотя бы один MCP-сервер (иначе зона пуста).
    """
    resolvers = [m.mcp_token_resolver for m in modules if m.mcp_token_resolver is not None]
    if not resolvers:
        raise RuntimeError(
            "mount_mcp_servers: ни один модуль не поставил mcp_token_resolver "
            "(ожидался auth-модуль) — MCP-серверы остались бы без auth"
        )
    if len(resolvers) > 1:
        raise RuntimeError(
            f"mount_mcp_servers: несколько mcp_token_resolver ({len(resolvers)}) — "
            "ожидался ровно один (auth-модуль)"
        )
    return resolvers[0]


def mount_mcp_servers(
    app, modules: Sequence[Module], config: Config
) -> list[AbstractAsyncContextManager[None]]:
    """Смонтировать MCP-серверы всех модулей под ``/mcp/<code>``.

    Возвращает lifespan-CM каждого подприложения — ``create_app`` входит в них
    через ``AsyncExitStack`` (инициализация session-manager форка). Дубль ``code``
    между модулями → ``RuntimeError`` (громкий отказ, не тихий перезатёр).
    """
    # Импорт fastmcp-кода — здесь, не на верхнем уровне (backend-only граница).
    from starlette.middleware import Middleware as ASGIMiddleware
    from starlette.middleware.trustedhost import TrustedHostMiddleware

    from src.core.mcp import (
        McpServerAuditMiddleware,
        McpServerContext,
        McpServerTokenVerifier,
    )

    pairs = [
        (code, builder)
        for m in modules
        for code, builder in m.mcp_servers.items()
    ]
    if not pairs:
        return []  # ни один модуль не объявил MCP-сервер — зона пуста

    ctx = McpServerContext(
        auth=McpServerTokenVerifier(_collect_resolver(modules)),
        audit=McpServerAuditMiddleware(),
        allowed_hosts=config.mcp_allowed_hosts_list,
    )
    # DNS-rebinding защита на ASGI-слое (форк не имеет TransportSecuritySettings).
    asgi_mw = (
        [ASGIMiddleware(TrustedHostMiddleware, allowed_hosts=ctx.allowed_hosts)]
        if ctx.allowed_hosts
        else None
    )

    lifespans: list[AbstractAsyncContextManager[None]] = []
    built: dict[str, object] = {}
    for code, builder in pairs:
        if code in built:
            raise RuntimeError(f"mount_mcp_servers: duplicate mcp server code: {code!r}")
        mcp = builder(ctx)
        # path="/" — иначе сабап слушает свой дефолт streamable_http_path="/mcp", и
        # под mount /mcp/<code> реальный эндпоинт уезжает в /mcp/<code>/mcp (307→404).
        # С "/" эндпоинт встаёт ровно на /mcp/<code> (точнее /mcp/<code>/ — Starlette
        # редиректит корень mount на trailing slash; MCP-клиент 307 отрабатывает).
        sub = mcp.http_app(
            path="/",
            transport="streamable-http",
            stateless_http=True,
            middleware=asgi_mw,
        )
        app.mount(f"{MCP_PREFIX}/{code}", sub)
        built[code] = mcp
        lifespans.append(sub.lifespan(sub))
        _LOG.info("mount_mcp_servers: mounted MCP server %r at %s/%s", code, MCP_PREFIX, code)

    # Живые FastMCP-инстансы на app.state — для интроспекции (info-страница, если
    # её добавит модуль, читает их без повторной сборки и без импорта fastmcp).
    app.state.mcp_servers = built
    return lifespans


__all__ = ["MCP_PREFIX", "mount_mcp_servers"]
