"""research MCP: note_create / notes_list (+kind) / note_get / note_update / note_delete."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db


async def _research(call) -> str:
    return (await call("research_create", title="R"))["code"]


async def test_note_create_returns_only_code(call):
    r = await _research(call)
    n = await call("note_create", research_code=r, kind="idea", title="N", description="d")
    assert list(n.keys()) == ["code"]
    assert n["code"].startswith("NOTE@")


async def test_note_create_unknown_kind_errors(call):
    r = await _research(call)
    with pytest.raises(ToolError, match="Unknown note kind"):
        await call("note_create", research_code=r, kind="bogus", title="N")


async def test_note_create_research_not_found(call):
    with pytest.raises(ToolError, match="Research .* not found"):
        await call("note_create", research_code="RESEARCH@missing000000000000", kind="idea", title="N")


async def test_notes_list_all_and_kind_filter(call):
    r = await _research(call)
    await call("note_create", research_code=r, kind="idea", title="I")
    await call("note_create", research_code=r, kind="question", title="Q")

    all_rows = (await call("notes_list", research_code=r))["result"]
    ideas = (await call("notes_list", research_code=r, kind="idea"))["result"]

    assert len(all_rows) == 2
    assert [x["title"] for x in ideas] == ["I"]
    assert set(all_rows[0]) == {"code", "kind", "title", "description", "updated_at"}


async def test_notes_list_bad_kind_errors(call):
    r = await _research(call)
    with pytest.raises(ToolError, match="Unknown note kind"):
        await call("notes_list", research_code=r, kind="bogus")


async def test_notes_list_research_not_found(call):
    with pytest.raises(ToolError, match="Research .* not found"):
        await call("notes_list", research_code="RESEARCH@missing000000000000")


async def test_note_get_full_with_body(call):
    r = await _research(call)
    n = (await call("note_create", research_code=r, kind="memory", title="N", body="# note body"))["code"]
    g = await call("note_get", note_code=n)
    assert g["kind"] == "memory" and g["body"] == "# note body"
    assert list(g.keys())[-1] == "updated_at"


async def test_note_get_not_found(call):
    with pytest.raises(ToolError, match="Note .* not found"):
        await call("note_get", note_code="NOTE@missing0000000000000")


async def test_note_update_fields(call):
    r = await _research(call)
    n = (await call("note_create", research_code=r, kind="idea", title="N"))["code"]
    await call("note_update", note_code=n, kind="result", title="N2")
    g = await call("note_get", note_code=n)
    assert g["kind"] == "result" and g["title"] == "N2"


async def test_note_update_bad_kind_errors(call):
    r = await _research(call)
    n = (await call("note_create", research_code=r, kind="idea", title="N"))["code"]
    with pytest.raises(ToolError, match="Unknown note kind"):
        await call("note_update", note_code=n, kind="bogus")


async def test_note_update_not_found(call):
    with pytest.raises(ToolError, match="Note .* not found"):
        await call("note_update", note_code="NOTE@missing0000000000000", title="z")


async def test_note_delete_true_then_false(call):
    r = await _research(call)
    n = (await call("note_create", research_code=r, kind="idea", title="N"))["code"]
    assert (await call("note_delete", note_code=n))["result"] is True
    assert (await call("note_delete", note_code=n))["result"] is False
