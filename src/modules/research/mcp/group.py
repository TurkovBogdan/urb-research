"""MCP-тулы групп — папок, по которым разложен реестр исследований.

Тонкий адаптер над CRUD. Группа стоит НАД исследованием и не участвует в пайплайне: у неё нет
ни тела, ни источников, ни статусов — агенту видна одна карточка (title/description). Всё, чем
группа выглядит и как стоит в списке (иконка, цвет, ``sort``), на этой поверхности не выставлено
вовсе — это выбор человека в интерфейсе. title/description режутся усечением в CRUD
(кириллица-safe), не ошибкой. Ошибка → ``ValueError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import strip_prefix
from src.modules.research.crud import group as group_crud
from src.modules.research.dto import AgentGroupCreated, AgentGroupScan

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def group_create(
        title: str,
        description: str | None = None,
    ) -> AgentGroupCreated:
        """Create a group — a folder that researches are filed in.

        A group carries no research content of its own: it only names a folder. Overlong
        fields are trimmed (no error on overflow).

        Args:
            title: Short group name (≤128 chars).
            description: One-line "what lives here" for scanning the list (≤512).
        """
        row = await group_crud.group_create(title=title, description=description)
        return AgentGroupCreated.model_validate(row)

    @mcp.tool()
    async def group_list() -> list[AgentGroupScan]:
        """List all groups in the order the user arranged them."""
        # Ключ задан явно: у агента и у веб-списка разные вопросы к порядку. Веб сортируется
        # тем, что человек выбрал в панели (по умолчанию — где недавно работали), а сюда
        # приезжает та расстановка, которую он выставил руками (`sort`) и которую агент
        # видит, но не меняет.
        rows = await group_crud.group_list(sort_by="sort", sort_dir="desc")
        return [AgentGroupScan.model_validate(r) for r in rows]

    @mcp.tool()
    async def group_get(group_code: str) -> AgentGroupScan:
        """Return one group. A group has no body — this is every field it has.

        Args:
            group_code: The group code returned by group_create / group_list.
        """
        group_code = strip_prefix(group_code)
        row = await group_crud.group_get(group_code)
        if row is None:
            raise ValueError(f"Group {group_code} not found.")
        return AgentGroupScan.model_validate(row)

    @mcp.tool()
    async def group_update(
        group_code: str,
        title: str | None = None,
        description: str | None = None,
    ) -> AgentGroupScan:
        """Update a group's fields (omit a field to keep it).

        Args:
            group_code: The group to update.
            title: New title (≤128), or omit to keep.
            description: New one-line description (≤512), or omit.
        """
        group_code = strip_prefix(group_code)
        row = await group_crud.group_update(group_code, title=title, description=description)
        if row is None:
            raise ValueError(f"Group {group_code} not found.")
        return AgentGroupScan.model_validate(row)

    @mcp.tool()
    async def group_delete(group_code: str) -> bool:
        """Delete a group. Returns true if it existed.

        NO CASCADE: the researches filed under it are kept and simply become ungrouped.

        Args:
            group_code: The group to delete.
        """
        return await group_crud.group_delete(strip_prefix(group_code))
