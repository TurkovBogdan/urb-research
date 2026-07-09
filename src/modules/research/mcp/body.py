"""MCP-тулы body-редактора — общие правки тела сущности по префиксу кода.

Диспетч и трансформы — в ``services/body.py``. Тело есть у ``RESEARCH@`` / ``AREA@`` / ``NOTE@``.
Оба тула возвращают ``BodyView`` (код + новое тело), чтобы агент видел результат правки.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.dto import BodyView
from src.modules.research.services import body as body_service

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def body_edit(
        code: str,
        action: str,
        text: str,
        find: str | None = None,
        heading: str | None = None,
    ) -> BodyView:
        """Edit the body of a RESEARCH@ / AREA@ / NOTE@ entity. Returns the updated body.

        Cite the sources you kept inline as SOURCE@<code> — they render as links in the user's
        interface. Only cite reviewed, kept sources; never invent a code.

        Actions:
        - `set` — replace the whole body with `text`.
        - `replace` — replace `find` with `text`; error unless `find` occurs exactly once.
        - `replace_block` — replace the `heading` (`#`/`##`) block (up to the next heading of
          equal-or-higher level) with `text`; error if the heading is not found.

        Args:
            code: The entity whose body to edit (RESEARCH@ / AREA@ / NOTE@; source/query have no body).
            action: One of set / replace / replace_block.
            text: The new text (whole body for set; replacement for replace / replace_block).
            find: The exact unique substring to replace (for `replace`).
            heading: The heading line, e.g. `## Findings` (for `replace_block`).
        """
        if action == "set":
            def mutate(body: str) -> str:
                return body_service.op_set(body, text=text)
        elif action == "replace":
            if find is None:
                raise ValueError("action 'replace' requires 'find'.")

            def mutate(body: str) -> str:
                return body_service.op_replace(body, find=find, text=text)
        elif action == "replace_block":
            if heading is None:
                raise ValueError("action 'replace_block' requires 'heading'.")

            def mutate(body: str) -> str:
                return body_service.op_replace_block(body, heading=heading, text=text)
        else:
            raise ValueError("action must be 'set', 'replace' or 'replace_block'.")

        row = await body_service.apply(code, mutate)
        return BodyView(code=code, body=row.body, updated_at=row.updated_at)

    @mcp.tool()
    async def body_add(
        code: str, text: str, position: str, anchor: str | None = None
    ) -> BodyView:
        """Add text to the body of a RESEARCH@ / AREA@ / NOTE@ entity. Returns the updated body.

        Cite the sources you kept inline as SOURCE@<code> — they render as links in the user's
        interface. Only cite reviewed, kept sources; never invent a code.

        Positions:
        - `start` / `end` — prepend / append to the whole body.
        - `before` / `after` — insert relative to `anchor` (a heading or a unique string).

        Args:
            code: The entity whose body to add to (RESEARCH@ / AREA@ / NOTE@).
            text: The text to add.
            position: One of start / end / before / after.
            anchor: The unique anchor string (required for before / after).
        """
        if position in ("start", "end"):
            def mutate(body: str) -> str:
                return body_service.op_append(body, text=text, position=position)
        elif position in ("before", "after"):
            if anchor is None:
                raise ValueError("position 'before'/'after' requires 'anchor'.")

            def mutate(body: str) -> str:
                return body_service.op_insert(body, text=text, anchor=anchor, position=position)
        else:
            raise ValueError("position must be 'start', 'end', 'before' or 'after'.")

        row = await body_service.apply(code, mutate)
        return BodyView(code=code, body=row.body, updated_at=row.updated_at)
