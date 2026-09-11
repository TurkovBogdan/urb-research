"""Presentation prefixes for readable entity codes — the research agent surface.

Prefixing is a research concern: research is the only module with an MCP surface, so it owns the
typed codes shown to the agent — its own (research / area / note / query / source) and the
web_search codes it references (search / page). web_search itself stores and returns bare codes.

A stored code (PK / FK / cross-module soft-ref) is a **bare hex hash** — the value
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

A research code is ``CODE_LEN`` hex chars; the ``RETIRED_CODE_LEN``-char form that predates
``rem_011_code_length`` resolves nowhere. ``checked_code`` / ``bare_code`` turn that into a
refusal that names the format instead of a bare "not found" — an agent holding a code from an
old transcript learns why it fails. web_search codes (``SEARCH@`` / ``PAGE@``) keep the long
form and never pass through these two.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import PlainSerializer

from src.modules.research.constants import CODE_LEN

RETIRED_CODE_LEN = 22

RETIRED_CODE_REFUSAL = (
    f"This code is in the retired {RETIRED_CODE_LEN}-char format and resolves to nothing — "
    f"a research code is now {CODE_LEN} hex chars (e.g. RESEARCH@279d8a77f1). Look the entity "
    "up again (research_list / areas_list / notes_list / sources_list) and use the code it "
    "returns; codes copied from an older transcript are gone for good."
)


def code_prefix(value: str) -> str:
    """Тип-слово входного кода (``AREA`` из ``AREA@<hash>``) для диспетча по уровню; ``""`` если голый."""
    return value.split("@", 1)[0] if "@" in value else ""


def strip_prefix(value: str | None) -> str | None:
    """Boundary → storage: drop a presentation prefix, leaving the bare hash.

    Idempotent on a bare code (a hex hash has no ``@`` → returned unchanged).
    """
    return value.rpartition("@")[2] if value else value


def _retired_format(value: str) -> bool:
    """Хвост кода — снятый с вооружения формат (``RETIRED_CODE_LEN`` hex-символов)."""
    tail = value.rpartition("@")[2]
    return len(tail) == RETIRED_CODE_LEN and all(c in "0123456789abcdef" for c in tail)


def checked_code(value: str) -> str:
    """Код research-сущности как есть; код снятого формата — отказ с объяснением."""
    if _retired_format(value):
        raise ValueError(RETIRED_CODE_REFUSAL)
    return value


def bare_code(value: str | None) -> str | None:
    """Граница → хранилище для кода research-сущности: ``strip_prefix`` + отказ старому формату."""
    return strip_prefix(checked_code(value)) if value else value


def tagged(prefix: str, value: str | None) -> str | None:
    """Storage → boundary: presentation form of a bare code (``AREA@<hash>``); ``None`` stays ``None``."""
    return value if value is None else f"{prefix}@{value}"


def prefixed(prefix: str):
    """Annotated ``str`` type whose JSON form carries ``prefix@`` (a bare hash on the wire in).

    ``prefix`` is the bare type word (``RESEARCH``/``SOURCE``/…); the ``@`` separator is added here,
    so the type name and the separator are not conflated in the constant.
    """
    return Annotated[
        str,
        PlainSerializer(
            lambda value: tagged(prefix, value), return_type=str, when_used="json"
        ),
    ]


__all__ = [
    "RETIRED_CODE_LEN",
    "RETIRED_CODE_REFUSAL",
    "bare_code",
    "checked_code",
    "code_prefix",
    "prefixed",
    "strip_prefix",
    "tagged",
]
