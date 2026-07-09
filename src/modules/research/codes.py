"""Presentation prefixes for readable entity codes — the research agent surface.

Prefixing is a research concern: research is the only module with an MCP surface, so it owns the
typed codes shown to the agent — its own (research / area / note / query / source) and the
web_search codes it references (search / page). web_search itself stores and returns bare codes.

A stored code (PK / FK / cross-module soft-ref) is a **bare 22-hex hash** — the value
``random_hash()`` / ``text_hash()`` produce. The type prefix (``RESEARCH@`` / ``SOURCE@`` /
``SEARCH@`` / …) is a **presentation** concern: it lets the agent (and a human in the UI) tell
one entity from another at a glance, and turns a free-floating code into a typed reference.
The wire form is ``type@hash`` — ``@`` reads as a namespaced reference and never occurs in a hash.

The prefix lives ONLY at the boundary — never in the database:

- **Output** (DTO → agent / API): a code field annotated with ``prefixed(PREFIX)`` serialises
  with the prefix (JSON only, so an internal ``model_dump()`` round-trip stays bare).
- **Input** (agent / API → code): ``strip_prefix`` drops it before the value reaches CRUD.

Because the hash alphabet is ``[0-9a-f]`` (no ``@``) and every prefix is joined with ``@``,
``strip_prefix`` is idempotent on an already-bare code — safe to apply to internal values too.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import PlainSerializer


def code_prefix(value: str) -> str:
    """Тип-слово входного кода (``AREA`` из ``AREA@<hash>``) для диспетча по уровню; ``""`` если голый."""
    return value.split("@", 1)[0] if "@" in value else ""


def strip_prefix(value: str | None) -> str | None:
    """Boundary → storage: drop a presentation prefix, leaving the bare hash.

    Idempotent on a bare code (a 22-hex hash has no ``@`` → returned unchanged).
    """
    return value.rpartition("@")[2] if value else value


def _tag(prefix: str, value: str | None) -> str | None:
    return value if value is None else f"{prefix}@{value}"


def prefixed(prefix: str):
    """Annotated ``str`` type whose JSON form carries ``prefix@`` (a bare hash on the wire in).

    ``prefix`` is the bare type word (``RESEARCH``/``SOURCE``/…); the ``@`` separator is added here,
    so the type name and the separator are not conflated in the constant.
    """
    return Annotated[
        str,
        PlainSerializer(
            lambda value: _tag(prefix, value), return_type=str, when_used="json"
        ),
    ]


__all__ = ["strip_prefix", "prefixed", "code_prefix"]
