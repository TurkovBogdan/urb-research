"""MCP-тул удаления — одна дверь для всех сущностей реестра.

Что удалять, говорит сам код: тип-слово префикса выбирает CRUD-функцию (так же диспетчеризует
по префиксу ``interface.py``). Пять отдельных тулов на одну строку кода каждый стоили агенту
пяти описаний в контексте, при том что отличается у них ровно одно — каскад, а он и так
привязан к типу и описан здесь одним списком.

Тип без удаления (``SOURCE@`` — источник разбирают или перекачивают; ``SEARCH@``/``PAGE@`` —
общий кэш web_search) и голый код без префикса упираются в один отказ, называющий пригодные
формы. Ошибка → ``ValueError`` (fastmcp превратит в ToolError).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.codes import bare_code, code_prefix
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    GROUP_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import group as group_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_query as source_query_crud

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP

_DELETE_BY_PREFIX = {
    RESEARCH_CODE_PREFIX: research_crud.research_delete,
    AREA_CODE_PREFIX: area_crud.area_delete,
    SOURCE_QUERY_CODE_PREFIX: source_query_crud.source_query_delete,
    NOTE_CODE_PREFIX: note_crud.note_delete,
    GROUP_CODE_PREFIX: group_crud.group_delete,
}

_NOTHING_TO_DELETE = (
    "code must be a RESEARCH@ / AREA@ / QUERY@ / NOTE@ / GROUP@ code — those are the entities "
    "that can be deleted. A source (SOURCE@) is reviewed with source_review or re-downloaded "
    "with sources_refetch, never deleted; SEARCH@ / PAGE@ are the shared web-search cache and "
    "are not removed from here either."
)


def _crud_delete(code: str):
    """Код → функция удаления его типа; тип без удаления (и голый код) — отказ с пригодными формами."""
    delete_entity = _DELETE_BY_PREFIX.get(code_prefix(code))
    if delete_entity is None:
        raise ValueError(_NOTHING_TO_DELETE)
    return delete_entity


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def delete(code: str) -> bool:
        """Delete one entity of any type. Returns true if it existed.

        The code decides both what is deleted and what goes down with it:
        RESEARCH@ — the research with its areas, notes, searches and the source rows beneath
        them (the material itself, held in web_search, is not removed);
        AREA@ — the area with its searches and sources;
        QUERY@ — the search run with its sources;
        NOTE@ — just the note;
        GROUP@ — the group alone, NO cascade: the researches filed under it are kept and simply
        become ungrouped.

        A source (SOURCE@) is not deletable — review it with source_review or re-download it
        with sources_refetch.

        Args:
            code: The entity to delete — a RESEARCH@ / AREA@ / QUERY@ / NOTE@ / GROUP@ code.
        """
        return await _crud_delete(code)(bare_code(code))
