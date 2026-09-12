"""research MCP: body_set / body_replace / body_set_section / body_add через MCP-клиент."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from src.modules.research.services.body import (
    PREVIEW_ELISION_MARK,
    PREVIEW_WINDOW_CHARS,
    SEAM_TEXT_PLACEHOLDER,
)

pytestmark = pytest.mark.db


async def _research(call, body: str = "") -> str:
    return (await call("research_create", title="R", body=body))["code"]


async def test_body_set_returns_a_receipt_without_the_body(call):
    code = await _research(call, body="old")
    receipt = await call("body_set", code=code, text="новое тело")

    assert receipt == {"code": code, "length": len("новое тело")}
    assert (await call("research_get", research_code=code))["body"] == "новое тело"


async def test_body_replace_single_returns_one_seam(call):
    research = await _research(call)
    area = (await call("area_create", research_code=research, title="A"))["code"]
    await call("body_set", code=area, text="alpha beta")
    r = await call("body_replace", code=area, find="beta", text="gamma")

    assert r == {"code": area, "replaced": 1, "edits": [f"alpha {SEAM_TEXT_PLACEHOLDER}"]}
    assert (await call("area_get", area_code=area))["body"] == "alpha gamma"


async def test_body_replace_single_refuses_a_repeated_find(call):
    code = await _research(call, body="a a")
    with pytest.raises(ToolError, match="occurs 2 times"):
        await call("body_replace", code=code, find="a", text="b")


async def test_body_replace_all_returns_a_seam_per_occurrence(call):
    code = await _research(call, body="a b a b a")
    r = await call("body_replace", code=code, find="a", text="c", mode="all")

    assert r["replaced"] == 3 == len(r["edits"])
    assert all(seam.count(SEAM_TEXT_PLACEHOLDER) == 1 for seam in r["edits"])
    assert r["edits"][1] == f"a b {SEAM_TEXT_PLACEHOLDER} b a"
    assert (await call("research_get", research_code=code))["body"] == "c b c b c"


async def test_body_replace_never_echoes_the_text_it_was_given(call):
    code = await _research(call, body="alpha beta")
    r = await call("body_replace", code=code, find="beta", text="ЗАМЕНА" * 50)

    assert all("ЗАМЕНА" not in seam for seam in r["edits"])


async def test_body_replace_not_found(call):
    code = await _research(call, body="x")
    with pytest.raises(ToolError, match="not found in body"):
        await call("body_replace", code=code, find="z", text="y", mode="all")


async def test_body_replace_bad_mode(call):
    code = await _research(call, body="x")
    with pytest.raises(ToolError, match="mode must be"):
        await call("body_replace", code=code, find="x", text="y", mode="every")


async def test_body_set_section_on_note_returns_the_removed_block(call):
    research = await _research(call)
    note = (await call("note_create", research_code=research, kind="idea", title="N",
                       body="# A\nx\n## B\ny"))["code"]
    r = await call("body_set_section", code=note, heading="## B", text="## B2\nz")

    assert r == {"code": note, "removed": "## B\ny", "removed_length": 6, "stopped_at": None}
    assert (await call("note_get", note_code=note))["body"] == "# A\nx\n## B2\nz"


async def test_body_set_section_previews_a_long_block_and_names_its_length(call):
    block = "## A\n" + "z" * 400 + "\nконец раздела"
    code = await _research(call, body=f"{block}\n## B\nb")
    r = await call("body_set_section", code=code, heading="## A", text="## A2")

    assert r["removed_length"] == len(block)
    assert PREVIEW_ELISION_MARK in r["removed"]
    assert len(r["removed"]) == PREVIEW_WINDOW_CHARS * 2 + len(PREVIEW_ELISION_MARK)
    assert r["removed"].endswith("конец раздела")
    assert r["stopped_at"] == "## B"


async def test_body_set_section_keeps_a_fenced_comment_out_of_the_boundary(call):
    code = await _research(call, body="## A\n```python\n# считаем\nn = 1\n```\ntail\n## B\nb")
    r = await call("body_set_section", code=code, heading="## A", text="## A2")

    assert r["stopped_at"] == "## B"
    assert (await call("research_get", research_code=code))["body"] == "## A2\n## B\nb"


async def test_body_set_section_refuses_a_repeated_heading(call):
    code = await _research(call, body="## A\n### x\n1\n## B\n### x\n2")
    with pytest.raises(ToolError, match="occurs 2 times in the body"):
        await call("body_set_section", code=code, heading="### x", text="y")


async def test_body_set_section_path_picks_the_named_one(call):
    code = await _research(call, body="## A\n### x\n1\n## B\n### x\n2")
    r = await call("body_set_section", code=code, heading="## B > ### x", text="### x\nнового")

    assert r["removed"] == "### x\n2"
    assert (await call("research_get", research_code=code))["body"] == "## A\n### x\n1\n## B\n### x\nнового"


async def test_body_set_section_path_segment_must_be_a_heading(call):
    code = await _research(call, body="## A\n### x\n1")
    with pytest.raises(ToolError, match="is not a markdown heading"):
        await call("body_set_section", code=code, heading="A > ### x", text="y")


async def test_body_tool_refuses_an_unsupported_prefix(call):
    with pytest.raises(ToolError, match="not supported"):
        await call("body_set", code="SOURCE@x000000000", text="x")


async def test_body_tool_reports_a_missing_entity(call):
    with pytest.raises(ToolError, match="not found"):
        await call("body_set", code="RESEARCH@missing00", text="x")


async def test_body_add_start_end(call):
    code = await _research(call, body="MID")
    await call("body_add", code=code, text="PRE ", position="start")
    r = await call("body_add", code=code, text=" POST", position="end")

    assert r == {"code": code, "edit": f"PRE MID{SEAM_TEXT_PLACEHOLDER}"}
    assert (await call("research_get", research_code=code))["body"] == "PRE MID POST"


async def test_body_add_before_after_anchor(call):
    code = await _research(call, body="XY")
    r = await call("body_add", code=code, text="_", position="after", anchor="X")

    assert r["edit"] == f"X{SEAM_TEXT_PLACEHOLDER}Y"
    assert (await call("research_get", research_code=code))["body"] == "X_Y"


async def test_body_add_missing_anchor(call):
    code = await _research(call, body="XY")
    with pytest.raises(ToolError, match="requires 'anchor'"):
        await call("body_add", code=code, text="_", position="before")


async def test_body_add_bad_position(call):
    code = await _research(call)
    with pytest.raises(ToolError, match="position must be"):
        await call("body_add", code=code, text="_", position="sideways")
