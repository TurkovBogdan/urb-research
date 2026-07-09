"""research MCP: body_edit / body_add через MCP-клиент (диспетч по префиксу, ошибки)."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db


async def _research(call, body: str = "") -> str:
    return (await call("research_create", title="R", body=body))["code"]


async def test_body_edit_set_echoes_code_and_persists(call):
    code = await _research(call, body="old")
    r = await call("body_edit", code=code, action="set", text="new")
    assert r["code"] == code and r["body"] == "new"
    assert list(r.keys())[-1] == "updated_at"
    assert (await call("research_get", research_code=code))["body"] == "new"


async def test_body_edit_replace_on_area(call):
    research = await _research(call)
    area = (await call("area_create", research_code=research, title="A"))["code"]
    await call("body_edit", code=area, action="set", text="alpha beta")
    r = await call("body_edit", code=area, action="replace", find="beta", text="gamma")
    assert r["body"] == "alpha gamma"


async def test_body_edit_replace_block_on_note(call):
    research = await _research(call)
    note = (await call("note_create", research_code=research, kind="idea", title="N",
                       body="# A\nx\n## B\ny"))["code"]
    r = await call("body_edit", code=note, action="replace_block", heading="## B", text="## B2\nz")
    assert r["body"] == "# A\nx\n## B2\nz"


async def test_body_edit_replace_missing_find_arg(call):
    code = await _research(call, body="x")
    with pytest.raises(ToolError, match="requires 'find'"):
        await call("body_edit", code=code, action="replace", text="y")


async def test_body_edit_replace_not_unique(call):
    code = await _research(call, body="a a")
    with pytest.raises(ToolError, match="must be unique"):
        await call("body_edit", code=code, action="replace", find="a", text="b")


async def test_body_edit_replace_block_missing_heading_arg(call):
    code = await _research(call, body="# A\nx")
    with pytest.raises(ToolError, match="requires 'heading'"):
        await call("body_edit", code=code, action="replace_block", text="y")


async def test_body_edit_bad_action(call):
    code = await _research(call)
    with pytest.raises(ToolError, match="action must be"):
        await call("body_edit", code=code, action="frobnicate", text="x")


async def test_body_edit_unsupported_prefix(call):
    with pytest.raises(ToolError, match="not supported"):
        await call("body_edit", code="SOURCE@x0000000000000000000", action="set", text="x")


async def test_body_edit_not_found(call):
    with pytest.raises(ToolError, match="not found"):
        await call("body_edit", code="RESEARCH@missing000000000000", action="set", text="x")


async def test_body_add_start_end(call):
    code = await _research(call, body="MID")
    await call("body_add", code=code, text="PRE ", position="start")
    r = await call("body_add", code=code, text=" POST", position="end")
    assert r["body"] == "PRE MID POST"


async def test_body_add_before_after_anchor(call):
    code = await _research(call, body="XY")
    r = await call("body_add", code=code, text="_", position="after", anchor="X")
    assert r["body"] == "X_Y"


async def test_body_add_missing_anchor(call):
    code = await _research(call, body="XY")
    with pytest.raises(ToolError, match="requires 'anchor'"):
        await call("body_add", code=code, text="_", position="before")


async def test_body_add_bad_position(call):
    code = await _research(call)
    with pytest.raises(ToolError, match="position must be"):
        await call("body_add", code=code, text="_", position="sideways")
