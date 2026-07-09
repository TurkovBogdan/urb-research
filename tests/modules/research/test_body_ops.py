"""research: чистые трансформы body-редактора (``services/body.py``) — без БД."""

from __future__ import annotations

import pytest

from src.modules.research.services import body

pytestmark = pytest.mark.pure


def test_op_set_replaces_whole():
    assert body.op_set("old", text="new") == "new"


def test_op_append_start_and_end():
    assert body.op_append("B", text="A", position="start") == "AB"
    assert body.op_append("B", text="A", position="end") == "BA"


def test_op_append_bad_position():
    with pytest.raises(ValueError, match="'start' or 'end'"):
        body.op_append("B", text="A", position="middle")


def test_op_replace_unique():
    assert body.op_replace("a b a", find="b", text="c") == "a c a"


def test_op_replace_not_found():
    with pytest.raises(ValueError, match="not found"):
        body.op_replace("abc", find="z", text="y")


def test_op_replace_not_unique():
    with pytest.raises(ValueError, match="must be unique"):
        body.op_replace("a a", find="a", text="b")


def test_op_insert_before_and_after():
    assert body.op_insert("XY", text="_", anchor="Y", position="before") == "X_Y"
    assert body.op_insert("XY", text="_", anchor="X", position="after") == "X_Y"


def test_op_insert_anchor_missing():
    with pytest.raises(ValueError, match="not found"):
        body.op_insert("XY", text="_", anchor="Z", position="before")


def test_op_insert_anchor_not_unique():
    with pytest.raises(ValueError, match="unique"):
        body.op_insert("aa", text="_", anchor="a", position="after")


def test_op_replace_block_up_to_same_level():
    src = "# A\nx\n## B\ny\n# C\nz"
    assert body.op_replace_block(src, heading="## B", text="## B2\nnew") == "# A\nx\n## B2\nnew\n# C\nz"


def test_op_replace_block_swallows_lower_subsections():
    src = "## A\nx\n### sub\ns\n## B\ny"
    assert body.op_replace_block(src, heading="## A", text="## A2") == "## A2\n## B\ny"


def test_op_replace_block_not_found():
    with pytest.raises(ValueError, match="not found"):
        body.op_replace_block("# A\nx", heading="## Z", text="y")


def test_op_replace_block_requires_heading():
    with pytest.raises(ValueError, match="not a markdown heading"):
        body.op_replace_block("# A", heading="plain", text="y")
