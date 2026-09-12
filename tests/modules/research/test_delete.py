"""research MCP: ``delete`` — одна дверь на все типы, разбор по префиксу кода.

Каскады каждого типа проверяют тесты своей сущности (``test_research`` / ``test_area`` /
``test_note`` / ``test_search_sources`` / ``test_group_mcp``); здесь — сам диспетч: что тул
принимает, чем отвечает на неудаляемый тип и на код без префикса, и что пяти прежних тулов
на поверхности больше нет.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from src.modules.research.codes import RETIRED_CODE_LEN
from src.modules.research.constants import CODE_LEN

pytestmark = pytest.mark.db

_HASH = "0" * CODE_LEN


@pytest.mark.parametrize(
    "code",
    [f"SOURCE@{_HASH}", f"SEARCH@{_HASH}", f"PAGE@{_HASH}", _HASH],
    ids=["source", "search", "page", "no-prefix"],
)
async def test_a_code_that_deletes_nothing_is_refused_by_naming_what_does(call, code):
    with pytest.raises(ToolError, match=r"RESEARCH@ / AREA@ / QUERY@ / NOTE@ / GROUP@"):
        await call("delete", code=code)


async def test_a_source_is_told_to_be_reviewed_or_refetched(call):
    with pytest.raises(ToolError, match="source_review.*sources_refetch"):
        await call("delete", code=f"SOURCE@{_HASH}")


async def test_a_retired_code_is_answered_with_the_format(call):
    with pytest.raises(ToolError, match="retired 22-char format"):
        await call("delete", code="RESEARCH@" + "b" * RETIRED_CODE_LEN)


async def test_the_type_tag_is_what_picks_the_entity(call):
    """Тул диспетчеризует префиксом — исследование удаляется по своему коду, как его вернул create."""
    research = (await call("research_create", title="R"))["code"]

    assert (await call("delete", code=research))["result"] is True
    assert (await call("research_list"))["result"] == []


async def test_the_five_entity_deletes_left_the_surface(mcp):
    names = {tool.name for tool in await mcp.list_tools()}

    assert "delete" in names
    assert not names & {
        "research_delete",
        "area_delete",
        "note_delete",
        "group_delete",
        "query_search_delete",
    }
