"""MCP-тул показа сущности человеку — открыть её страницу в браузере пользователя.

Единственный мост «агент → глаза пользователя»: любой код системы превращается в адрес
страницы приложения и открывается локальным браузером. Приложение локальное, бэкенд раздаёт
собранный SPA сам, поэтому адрес строится от ``server_host``/``server_port`` — тот же базовый
url, что открывает stdio-шим (``apps/app/mcp_stdio.py``).

Раздел адреса выбирается по префиксу кода. Research-маршруты несут код **с префиксом** (так же
строит ссылки сам фронт: ``/research/sources/SOURCE@…``), web_search-маршруты — голый: коды
типизирует research, сам web_search их не префиксует (см. ``research.codes``).
"""

from __future__ import annotations

import asyncio
import webbrowser
from typing import TYPE_CHECKING

from src.core.config import get_config
from src.modules.research.codes import code_prefix, strip_prefix
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    GROUP_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    PAGE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP

_RESEARCH_SECTION = {
    GROUP_CODE_PREFIX: "researches",  # полка и исследование делят сегмент, разводит префикс
    RESEARCH_CODE_PREFIX: "researches",
    AREA_CODE_PREFIX: "areas",
    NOTE_CODE_PREFIX: "notes",
    SOURCE_QUERY_CODE_PREFIX: "queries",
    SOURCE_DOCUMENT_CODE_PREFIX: "sources",
}

_WEB_SEARCH_SECTION = {
    SEARCH_CODE_PREFIX: "queries",
    PAGE_CODE_PREFIX: "pages",
}


def _page_path(code: str) -> str:
    """Код → путь страницы приложения; неизвестный тип кода — ошибка."""
    prefix = code_prefix(code)
    if prefix in _RESEARCH_SECTION:
        return f"/research/{_RESEARCH_SECTION[prefix]}/{code}"
    if prefix in _WEB_SEARCH_SECTION:
        return f"/web-search/{_WEB_SEARCH_SECTION[prefix]}/{strip_prefix(code)}"
    raise ValueError(
        "code must be a RESEARCH@ / AREA@ / NOTE@ / QUERY@ / SOURCE@ / GROUP@ / SEARCH@ / PAGE@ code."
    )


def _app_url(path: str) -> str:
    config = get_config()
    host = config.server_host if config.server_host not in ("", "0.0.0.0") else "127.0.0.1"
    return f"http://{host}:{config.server_port}{path}"


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def interface_open(code: str) -> str:
        """Open the page for any code in the user's browser and return its address.

        This is how you SHOW something instead of describing it — hand the user the actual
        research, area, note, search or source on screen. Use it when the user asks to see or
        open something, and after you finish a piece of work worth looking at. Returning the
        address also lets you paste it into the chat.

        Opening a page is a visible action on the user's machine: do it when it was asked for or
        clearly helps, not after every call. If there is no browser to open (a headless host),
        the call fails with the address in the message — pass that address to the user instead.

        Args:
            code: Any entity code — RESEARCH@ / AREA@ / NOTE@ / QUERY@ / SOURCE@ / GROUP@ (a
                research entity) or SEARCH@ / PAGE@ (a web-search run or a fetched page).
        """
        url = _app_url(_page_path(code))
        # Запуск браузера — синхронный вызов неизвестной длительности (спавн процесса,
        # холодный старт): в потоке, чтобы не держать событийный цикл сервера.
        if not await asyncio.to_thread(webbrowser.open, url):
            raise ValueError(f"No browser to open on this host — give the user {url} instead.")
        return url
