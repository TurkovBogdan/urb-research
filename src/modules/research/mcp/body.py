"""MCP-тулы body-редактора — общие правки тела сущности по префиксу кода.

Диспетч и трансформы — в ``services/body.py``. Тело есть у ``RESEARCH@`` / ``AREA@`` / ``NOTE@``.
Оба тула возвращают ``AgentBodyView`` (код + новое тело), чтобы агент видел результат правки.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.dto import AgentBodyView
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
    ) -> AgentBodyView:
        """Edit the body of a RESEARCH@ / AREA@ / NOTE@ entity. Returns the updated body.

        Any code written into a body — a source you kept, a sibling area, a note, a search —
        renders as a link to that entity in the user's interface. Write it plain: no backticks,
        quotes, brackets or escaping. Only cite reviewed, kept sources; never invent a code.

        Writing your first body here? Call skill_get('body-markup') first — it is the markup this
        app actually renders (codes as links, no images, no raw HTML) and it takes one call.
        Adding a diagram? Call skill_get('mermaid') first: a `mermaid` fence renders as a real
        diagram, but unsupported syntax degrades to a code block without saying so. Put a unique
        heading above each diagram — then replace_block on that heading redraws exactly it.

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
        return AgentBodyView(code=code, body=row.body, updated_at=row.updated_at)

    @mcp.tool()
    async def body_add(
        code: str, text: str, position: str, anchor: str | None = None
    ) -> AgentBodyView:
        """Add text to the body of a RESEARCH@ / AREA@ / NOTE@ entity. Returns the updated body.

        Any code written into a body — a source you kept, a sibling area, a note, a search —
        renders as a link to that entity in the user's interface. Write it plain: no backticks,
        quotes, brackets or escaping. Only cite reviewed, kept sources; never invent a code.

        Writing your first body here? Call skill_get('body-markup') first — it is the markup this
        app actually renders (codes as links, no images, no raw HTML) and it takes one call.
        Adding a diagram? Call skill_get('mermaid') first: a `mermaid` fence renders as a real
        diagram, but unsupported syntax degrades to a code block without saying so. Put a unique
        heading above each diagram — then replace_block on that heading redraws exactly it.

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
        return AgentBodyView(code=code, body=row.body, updated_at=row.updated_at)
