"""research: чистые трансформы body-редактора (``services/body.py``) — без БД."""

from __future__ import annotations

import pytest

from src.modules.research.services import body

pytestmark = pytest.mark.pure

FENCED = "\n".join(
    [
        "## Обзор",
        "",
        "Вводный текст.",
        "",
        "```python",
        "# считаем строки",
        "n = len(rows)",
        "```",
        "",
        "Продолжение того же раздела.",
        "",
        "## Следующий раздел",
        "",
        "Хвост.",
    ]
)

REPEATED_HEADING = "\n".join(
    [
        "## Токены",
        "",
        "### API calls",
        "про токены",
        "",
        "## Лимиты",
        "",
        "### API calls",
        "про лимиты",
    ]
)


WINDOW = body.PREVIEW_WINDOW_CHARS
PLACEHOLDER = body.SEAM_TEXT_PLACEHOLDER


def test_op_set_replaces_whole():
    assert body.op_set("old", text="new") == "new"


def test_op_append_start_and_end():
    assert body.op_append("B", text="A", position="start") == ("AB", f"{PLACEHOLDER}B")
    assert body.op_append("B", text="A", position="end") == ("BA", f"B{PLACEHOLDER}")


def test_op_append_bad_position():
    with pytest.raises(ValueError, match="'start' or 'end'"):
        body.op_append("B", text="A", position="middle")


def test_seam_at_the_start_of_a_long_body_has_no_leading_mark():
    """Край тела виден по тому, что окно кончилось; ``…`` тут значил бы обрезку и вводил в
    заблуждение."""
    edited, seam = body.op_append("z" * 500, text="A", position="start")

    assert seam == f"{PLACEHOLDER}{'z' * WINDOW}…"
    assert edited.startswith("Az")


def test_seam_at_the_end_of_a_long_body_has_no_trailing_mark():
    _, seam = body.op_append("z" * 500, text="A", position="end")

    assert seam == f"…{'z' * WINDOW}{PLACEHOLDER}"


def test_seam_in_the_middle_is_marked_on_both_sides():
    _, seam = body.op_insert("a" * 500 + "|" + "b" * 500, text="_", anchor="|", position="before")

    assert seam == f"…{'a' * WINDOW}{PLACEHOLDER}|{'b' * (WINDOW - 1)}…"


def test_seam_windows_stop_at_the_window_size():
    _, seam = body.op_insert("a" * 500 + "|" + "b" * 500, text="_", anchor="|", position="after")

    assert seam.count(PLACEHOLDER) == 1
    assert len(seam.replace(PLACEHOLDER, "")) == WINDOW * 2 + len("……")


def test_op_replace_unique():
    assert body.op_replace("a b a", find="b", text="c") == ("a c a", [f"a {PLACEHOLDER} a"])


def test_op_replace_not_found():
    with pytest.raises(ValueError, match="not found"):
        body.op_replace("abc", find="z", text="y")


def test_op_replace_not_unique():
    with pytest.raises(ValueError, match="must be unique"):
        body.op_replace("a a", find="a", text="b")


def test_op_replace_all_returns_a_seam_per_occurrence():
    edited, seams = body.op_replace_all("a b a b a", find="a", text="c")

    assert edited == "c b c b c"
    assert seams == [
        f"{PLACEHOLDER} b a b a",
        f"a b {PLACEHOLDER} b a",
        f"a b a b {PLACEHOLDER}",
    ]


def test_op_replace_all_one_occurrence_is_still_one():
    assert body.op_replace_all("x y", find="y", text="z") == ("x z", [f"x {PLACEHOLDER}"])


def test_op_replace_all_ships_overlapping_windows_twice():
    """Соседние вхождения делят окрестность — общий текст едет в обоих швах, а не склеивается:
    склейка стоила бы соответствия «шов на вхождение»."""
    filler = "m" * 10
    edited, seams = body.op_replace_all(f"X{filler}X", find="X", text="Y")

    assert edited == f"Y{filler}Y"
    assert seams == [f"{PLACEHOLDER}{filler}X", f"X{filler}{PLACEHOLDER}"]
    assert all(filler in seam for seam in seams)


def test_op_replace_all_not_found():
    with pytest.raises(ValueError, match="not found"):
        body.op_replace_all("abc", find="z", text="y")


def test_op_insert_before_and_after():
    assert body.op_insert("XY", text="_", anchor="Y", position="before") == (
        "X_Y", f"X{PLACEHOLDER}Y"
    )
    assert body.op_insert("XY", text="_", anchor="X", position="after") == (
        "X_Y", f"X{PLACEHOLDER}Y"
    )


def test_op_insert_anchor_missing():
    with pytest.raises(ValueError, match="not found"):
        body.op_insert("XY", text="_", anchor="Z", position="before")


def test_op_insert_anchor_not_unique():
    with pytest.raises(ValueError, match="unique"):
        body.op_insert("aa", text="_", anchor="a", position="after")


def test_op_set_section_up_to_same_level():
    src = "# A\nx\n## B\ny\n# C\nz"
    edited, _ = body.op_set_section(src, heading="## B", text="## B2\nnew")
    assert edited == "# A\nx\n## B2\nnew\n# C\nz"


def test_op_set_section_swallows_lower_subsections():
    src = "## A\nx\n### sub\ns\n## B\ny"
    edited, cut = body.op_set_section(src, heading="## A", text="## A2")
    assert edited == "## A2\n## B\ny"
    assert cut.removed == "## A\nx\n### sub\ns"


def test_op_set_section_returns_the_block_it_removed():
    src = "## A\nx\n## B\ny"
    _, cut = body.op_set_section(src, heading="## A", text="## A2")
    assert cut.removed == "## A\nx"
    assert cut.removed_length == len("## A\nx")
    assert cut.stopped_at == "## B"


def test_op_set_section_reports_the_body_ending_the_block():
    src = "## A\nx\n## B\ny"
    _, cut = body.op_set_section(src, heading="## B", text="## B2")
    assert cut.removed == "## B\ny"
    assert cut.stopped_at is None


def test_op_set_section_elides_the_middle_of_a_long_block():
    """Длинный вырез приезжает головой и хвостом: хвост и есть ответ на «докуда дорезало»."""
    block = "## A\n" + "z" * 400 + "\nend of the section"
    src = f"{block}\n## B\ny"
    _, cut = body.op_set_section(src, heading="## A", text="## A2")

    assert cut.removed == f"{block[:WINDOW]}{body.PREVIEW_ELISION_MARK}{block[-WINDOW:]}"
    assert cut.removed.endswith("end of the section")
    assert cut.removed_length == len(block)


def test_op_set_section_returns_a_short_block_whole():
    block = "## A\n" + "z" * (WINDOW * 2 - len("## A\n"))
    _, cut = body.op_set_section(f"{block}\n## B", heading="## A", text="## A2")

    assert cut.removed == block
    assert body.PREVIEW_ELISION_MARK not in cut.removed
    assert cut.removed_length == WINDOW * 2


def test_op_set_section_returns_a_block_of_exactly_two_windows_whole():
    """Граница включительно: на ровно двух окнах половины ещё не перекрываются."""
    block = "#" * 2 + " " + "z" * (WINDOW * 2 - 3)
    _, cut = body.op_set_section(f"{block}\n## B", heading=block, text="## A2")

    assert cut.removed_length == WINDOW * 2
    assert cut.removed == block


def test_op_set_section_elides_a_block_one_char_over_two_windows():
    block = "#" * 2 + " " + "z" * (WINDOW * 2 - 2)
    _, cut = body.op_set_section(f"{block}\n## B", heading=block, text="## A2")

    assert cut.removed_length == WINDOW * 2 + 1
    assert body.PREVIEW_ELISION_MARK in cut.removed


def test_op_set_section_not_found():
    with pytest.raises(ValueError, match="not found"):
        body.op_set_section("# A\nx", heading="## Z", text="y")


def test_op_set_section_requires_heading():
    with pytest.raises(ValueError, match="not a markdown heading"):
        body.op_set_section("# A", heading="plain", text="y")


def test_op_set_section_matches_the_level_too():
    with pytest.raises(ValueError, match="not found"):
        body.op_set_section("### Про рыбок\nx", heading="## Про рыбок", text="y")


def test_op_set_section_ignores_a_heading_inside_a_fence():
    """Комментарий в ```` ```python ````-блоке — не заголовок: раздел не должен обрываться на
    нём, оставляя внизу половину секции и осиротевший закрывающий фенс."""
    edited, cut = body.op_set_section(FENCED, heading="## Обзор", text="## Обзор\n\nНовый текст.\n")

    assert edited == "## Обзор\n\nНовый текст.\n\n## Следующий раздел\n\nХвост."
    assert cut.stopped_at == "## Следующий раздел"
    assert "```" not in edited
    assert cut.removed.count("```") == 2


def test_op_set_section_ignores_a_heading_inside_a_tilde_fence():
    src = "\n".join(["## A", "~~~", "# not a heading", "~~~", "tail", "## B", "y"])
    edited, cut = body.op_set_section(src, heading="## A", text="## A2")

    assert edited == "## A2\n## B\ny"
    assert cut.removed == "## A\n~~~\n# not a heading\n~~~\ntail"


def test_op_set_section_finds_a_heading_after_a_closed_fence():
    src = "\n".join(["## A", "```", "# code", "```", "## B", "y"])
    edited, _ = body.op_set_section(src, heading="## B", text="## B2")

    assert edited == "## A\n```\n# code\n```\n## B2"


def test_op_set_section_refuses_a_repeated_heading_with_its_count():
    with pytest.raises(ValueError, match="occurs 2 times in the body"):
        body.op_set_section(REPEATED_HEADING, heading="### API calls", text="x")


def test_op_set_section_refusal_shows_a_path_from_the_body():
    with pytest.raises(ValueError, match=r"'## Токены > ### API calls'"):
        body.op_set_section(REPEATED_HEADING, heading="### API calls", text="x")


def test_op_set_section_says_when_no_path_can_help():
    """Дубликаты, которых не разводит ни один объемлющий заголовок: обещать путь тут — врать."""
    with pytest.raises(ValueError, match="no enclosing heading tells these apart"):
        body.op_set_section("## A\nx\n## A\ny", heading="## A", text="z")


def test_op_set_section_path_picks_the_named_one():
    edited, cut = body.op_set_section(
        REPEATED_HEADING, heading="## Лимиты > ### API calls", text="### API calls\nновое"
    )

    assert cut.removed == "### API calls\nпро лимиты"
    assert edited.endswith("## Лимиты\n\n### API calls\nновое")
    assert "про токены" in edited


def test_op_set_section_path_reaches_any_depth():
    src = "\n".join(["# A", "## B", "### C", "#### D", "d", "## E", "e"])
    edited, cut = body.op_set_section(src, heading="# A > ## B > ### C > #### D", text="#### D2")

    assert cut.removed == "#### D\nd"
    assert edited == "# A\n## B\n### C\n#### D2\n## E\ne"


def test_op_set_section_path_skips_intermediate_levels():
    """Сегмент ищется на любой глубине блока предыдущего, а не только среди прямых детей."""
    src = "\n".join(["## A", "### mid", "#### deep", "d", "## B", "b"])
    edited, _ = body.op_set_section(src, heading="## A > #### deep", text="#### deep2")

    assert edited == "## A\n### mid\n#### deep2\n## B\nb"


def test_op_set_section_path_segment_must_be_a_heading():
    with pytest.raises(ValueError, match="'Лимиты' is not a markdown heading"):
        body.op_set_section(REPEATED_HEADING, heading="Лимиты > ### API calls", text="x")


def test_op_set_section_path_segment_missing_inside_its_parent():
    with pytest.raises(ValueError, match="not found inside '## Токены'"):
        body.op_set_section(REPEATED_HEADING, heading="## Токены > ### Лимиты", text="x")


def test_op_set_section_path_refuses_a_repeat_inside_the_parent():
    src = "\n".join(["## A", "### x", "1", "### x", "2", "## B"])
    with pytest.raises(ValueError, match=r"occurs 2 times inside '## A'"):
        body.op_set_section(src, heading="## A > ### x", text="y")
