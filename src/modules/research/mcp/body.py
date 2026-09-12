"""MCP-тулы body-редактора — общие правки тела сущности по префиксу кода.

Диспетч и трансформы — в ``services/body.py``. Тело есть у ``RESEARCH@`` / ``AREA@`` / ``NOTE@``.

Что тул возвращает, решено по одному правилу: то, чего агент ещё не знает. Присланный им текст
назад не едет ни в каком виде — ни сам по себе, ни в составе тела. Вместо него **шов**: окно
тела по обе стороны от вставки с заглушкой на месте текста. Исключения два: ``body_set``
отдаёт расписку (тело целиком и есть присланный текст, шва там нет), а ``body_set_section`` —
предпросмотр вырезанного, потому что непредсказуем там не стык, а размах выреза.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import checked_code
from src.modules.research.dto import (
    AgentBodyAdded,
    AgentBodyReplaced,
    AgentBodySectionSet,
    AgentBodySet,
)
from src.modules.research.services import body as body_service

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def body_set(code: str, text: str) -> AgentBodySet:
        """Replace the whole body of a RESEARCH@ / AREA@ / NOTE@ entity with `text`.

        Markup — skill_get('body-markup'); a diagram in it — skill_get('mermaid').

        Returns a receipt only — the new length in characters, since the body is the text you
        just sent. To amend part of a body, use body_replace / body_set_section / body_add
        instead of rewriting it whole.

        Args:
            code: The entity whose body to replace (RESEARCH@ / AREA@ / NOTE@; searches and
                sources have no editable body).
            text: The new body in markdown — everything there now is discarded.
                Markup rules — skill_get('body-markup'); a diagram in it — skill_get('mermaid').
        """
        row = await body_service.apply(
            checked_code(code), lambda body: body_service.op_set(body, text=text)
        )
        return AgentBodySet(code=code, length=len(row.body or ""))

    @mcp.tool()
    async def body_replace(
        code: str, find: str, text: str, mode: str = "single"
    ) -> AgentBodyReplaced:
        """Replace the exact string `find` with `text` in the body of a RESEARCH@ / AREA@ / NOTE@.

        Markup — skill_get('body-markup'); a diagram in it — skill_get('mermaid').

        - `single` (default) — `find` must occur exactly once, or the call fails naming how many
          times it occurs.
        - `all` — replaces every occurrence. `find` occurring nowhere is an error in both modes.

        Returns `edits`: one seam per occurrence, in document order — 128 characters of the body
        either side of the edit, with `<text>` standing in for what you sent (`…` at an end marks
        a window cut short mid-body). `replaced` is how many, and matches the length of `edits`.

        Args:
            code: The entity whose body to edit (RESEARCH@ / AREA@ / NOTE@).
            find: The exact substring to replace, as it stands in the body.
            text: The replacement.
                Markup rules — skill_get('body-markup'); a diagram in it — skill_get('mermaid').
            mode: `single` (exactly one occurrence) or `all` (every occurrence).
        """
        if mode == "single":
            def edit(body: str) -> tuple[str, list[str]]:
                return body_service.op_replace(body, find=find, text=text)
        elif mode == "all":
            def edit(body: str) -> tuple[str, list[str]]:
                return body_service.op_replace_all(body, find=find, text=text)
        else:
            raise ValueError("mode must be 'single' or 'all'.")

        _, seams = await body_service.apply_edit(checked_code(code), edit)
        return AgentBodyReplaced(code=code, replaced=len(seams), edits=seams)

    @mcp.tool()
    async def body_set_section(code: str, heading: str, text: str) -> AgentBodySectionSet:
        """Replace one heading section of a RESEARCH@ / AREA@ / NOTE@ body with `text`.

        Markup — skill_get('body-markup'); a diagram in it — skill_get('mermaid').

        The section runs from its heading line down to the next heading of equal or higher
        level, so it takes its own subsections with it. A `#` line inside a ``` or ~~~ fence is
        code, not a heading, and never ends a section.

        `heading` matches the heading line as a whole, level included, and must occur exactly
        once in the body; a heading that repeats is refused, naming the count. Say which one you
        mean with a path — `## Findings > ### Limits`: every segment carries its own `#`, ` > `
        between them, the first unique in the body and each later one unique anywhere inside the
        previous one's section.

        Returns what was cut, not what you wrote: the boundary is computed here, so the reach of
        the cut is the one thing you cannot predict. `removed` — a preview of the block (first
        and last 128 characters joined by ` … `; a short block comes whole), `removed_length` —
        its true length, `stopped_at` — the heading that ended it (null = end of body). A section
        you thought was 500 characters coming back as 4000 is a cut that ran past it. The preview
        is all there is — the cut text is stored nowhere, so notice it here or not at all.

        Args:
            code: The entity whose body to edit (RESEARCH@ / AREA@ / NOTE@).
            heading: The heading line, or the path to it (above) when it repeats.
            text: The whole new section, normally starting with the heading again — leave it out
                and the heading goes too. Spliced in verbatim, so end it with the blank line
                that separated the old section from the next heading.
                Markup rules — skill_get('body-markup'); a diagram in it — skill_get('mermaid').
        """
        _, cut = await body_service.apply_edit(
            checked_code(code),
            lambda body: body_service.op_set_section(body, heading=heading, text=text),
        )
        return AgentBodySectionSet(
            code=code,
            removed=cut.removed,
            removed_length=cut.removed_length,
            stopped_at=cut.stopped_at,
        )

    @mcp.tool()
    async def body_add(
        code: str, text: str, position: str, anchor: str | None = None
    ) -> AgentBodyAdded:
        """Add text to the body of a RESEARCH@ / AREA@ / NOTE@ entity.

        Markup — skill_get('body-markup'); a diagram in it — skill_get('mermaid').

        Positions:
        - `start` / `end` — prepend / append to the whole body.
        - `before` / `after` — insert relative to `anchor` (a heading or a unique string).

        Your text is spliced in verbatim: no newline and no blank line is added around it, at
        any position. Put the blank line you want at the start or the end of `text` yourself,
        or the addition runs into the neighbouring paragraph.

        Returns `edit`, the seam — 128 characters of the body either side of the insertion, with
        `<text>` standing in for what you sent (`…` marks a window cut short mid-body). Read it:
        it shows exactly what your text ran into.

        Args:
            code: The entity whose body to add to (RESEARCH@ / AREA@ / NOTE@).
            text: The text to add, carrying its own leading/trailing blank lines.
                Markup rules — skill_get('body-markup'); a diagram in it — skill_get('mermaid').
            position: One of start / end / before / after.
            anchor: The unique anchor string (required for before / after).
        """
        if position in ("start", "end"):
            def edit(body: str) -> tuple[str, str]:
                return body_service.op_append(body, text=text, position=position)
        elif position in ("before", "after"):
            if anchor is None:
                raise ValueError("position 'before'/'after' requires 'anchor'.")

            def edit(body: str) -> tuple[str, str]:
                return body_service.op_insert(body, text=text, anchor=anchor, position=position)
        else:
            raise ValueError("position must be 'start', 'end', 'before' or 'after'.")

        _, seam = await body_service.apply_edit(checked_code(code), edit)
        return AgentBodyAdded(code=code, edit=seam)
