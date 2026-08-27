"""MCP-тулы групп — полок, на которые разложен реестр исследований.

Тонкий адаптер над CRUD. Группа стоит НАД исследованием и не участвует в пайплайне: у неё нет
ни тела, ни источников, ни статусов — агенту видна одна карточка (title/description). Всё, чем
полка выглядит и как лежит в списке (иконка, цвет, ``sort``), на этой поверхности не выставлено
вовсе — это выбор человека в интерфейсе. title/description режутся усечением в CRUD
(кириллица-safe), не ошибкой. Ошибка → ``ValueError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import strip_prefix
from src.modules.research.crud import group as group_crud
from src.modules.research.dto import GroupCreated, GroupScan

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def group_create(
        title: str,
        description: str | None = None,
    ) -> GroupCreated:
        """Create a group — a shelf that researches are filed under.

        A group carries no research content of its own: it only labels a shelf. Overlong
        fields are trimmed (no error on overflow).

        Args:
            title: Short group name (≤128 chars).
            description: One-line "what lives here" for scanning the list (≤512).
        """
        row = await group_crud.group_create(title=title, description=description)
        return GroupCreated.model_validate(row)

    @mcp.tool()
    async def group_list() -> list[GroupScan]:
        """List all groups in the order the user sees them."""
        return [GroupScan.model_validate(r) for r in await group_crud.group_list()]

    @mcp.tool()
    async def group_get(group_code: str) -> GroupScan:
        """Return one group. A group has no body — this is every field it has.

        Args:
            group_code: The group code returned by group_create / group_list.
        """
        group_code = strip_prefix(group_code)
        row = await group_crud.group_get(group_code)
        if row is None:
            raise ValueError(f"Group {group_code} not found.")
        return GroupScan.model_validate(row)

    @mcp.tool()
    async def group_update(
        group_code: str,
        title: str | None = None,
        description: str | None = None,
    ) -> GroupScan:
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
        return GroupScan.model_validate(row)

    @mcp.tool()
    async def group_delete(group_code: str) -> bool:
        """Delete a group. Returns true if it existed.

        NO CASCADE: the researches filed under it are kept and simply become ungrouped.

        Args:
            group_code: The group to delete.
        """
        return await group_crud.group_delete(strip_prefix(group_code))
