"""research: края body-редактора — ввод, о котором не думали, когда писали трансформы.

Счастливый путь пинует ``test_body_ops``; здесь — пустой ``find``, незакрытый фенс, CRLF,
заголовки, которых markdown не обещал, и замена, содержащая то, что искали. Всё — чистые
функции ``services/body.py``, без БД.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.modules.research.services import body

pytestmark = pytest.mark.pure

REPO_ROOT = Path(__file__).resolve().parents[3]

PLACEHOLDER = body.SEAM_TEXT_PLACEHOLDER

# Окно шва — число, обещанное агенту в описании каждого body-тула («128 characters either
# side»), поэтому в тестах оно литералом: разъедься оно с константой — это и есть поломка
# контракта, а не подробность реализации.
PROMISED_WINDOW = 128

# Пустой ``find`` уводит ``_replacement_seams`` в цикл, который не двигает курсор: ``body.find("",
# at)`` возвращает ``at`` при любом ``at``. Проверять это в самом рантайме теста нельзя — процесс
# не вернётся, — поэтому вызов уезжает в ребёнка с потолком памяти: он умрёт за секунду вместо
# того, чтобы съесть машину.
_EMPTY_FIND_PROBE = """
import resource
resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
from src.modules.research.services import body
try:
    body.{op}({body!r}, find="", text="X")
except BaseException as exc:
    print("RESULT:" + type(exc).__name__)
else:
    print("RESULT:returned")
"""


def _outcome_of_an_empty_find(op: str, source: str) -> str:
    """Чем кончится трансформ с пустым ``find`` — имя исключения или ``returned``."""
    probe = subprocess.run(
        [sys.executable, "-c", _EMPTY_FIND_PROBE.format(op=op, body=source)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO_ROOT,
    )
    marker = "RESULT:"
    for line in probe.stdout.splitlines():
        if line.startswith(marker):
            return line[len(marker):]
    return f"no result (rc={probe.returncode}): {probe.stderr[-200:]}"


@pytest.mark.parametrize(
    ("op", "source"),
    [("op_replace_all", "abc"), ("op_replace", "")],
    ids=["all-mode-any-body", "single-mode-empty-body"],
)
def test_an_empty_find_is_refused_instead_of_looping_forever(op: str, source: str):
    """ДЕФЕКТ: ``find=""`` не отказ, а вечный цикл — ``_replacement_seams`` не двигает курсор.

    Через тул это ``body_replace(code, find="", text=...)``: в режиме ``all`` — на любом теле,
    в режиме ``single`` — на пустом (там ``"".count("") == 1``, то есть «единственное вхождение»).
    Вызов не возвращается никогда и растит список швов до исчерпания памяти — сервер MCP занят
    навсегда одним аргументом, который агент может прислать по опечатке.
    """
    assert _outcome_of_an_empty_find(op, source) == "ValueError"


def test_an_empty_find_is_refused_by_name_not_by_its_count():
    """Пустой ``find`` отказывается сам по себе, а не как «встретилось 4 раза».

    Счёт вхождений пустой строки — правда (в ``abc`` их четыре), но агенту он говорит
    «уточни запрос», тогда как уточнять нечего: аргумент пустой. Отказ должен называть причину.
    """
    with pytest.raises(ValueError, match="must not be empty"):
        body.op_replace("abc", find="", text="X")


# ── заголовки, которых markdown не обещал ────────────────────────────────────
def test_a_seventh_level_heading_is_still_a_section():
    """Уровень считается числом ``#`` без потолка: ``#######`` (семь) — заголовок седьмого
    уровня, хотя markdown таких не рисует. Обещание тула — «строка совпадает целиком, уровень
    включительно», и оно выполняется."""
    edited, cut = body.op_set_section(
        "####### deep\nx\n# top\ny", heading="####### deep", text="####### d2"
    )

    assert edited == "####### d2\n# top\ny"
    assert cut.stopped_at == "# top"


def test_a_seventh_level_heading_does_not_end_a_sixth_level_section():
    _, cut = body.op_set_section(
        "###### six\na\n####### seven\nb\n## two\nc", heading="###### six", text="R"
    )

    assert cut.removed == "###### six\na\n####### seven\nb"
    assert cut.stopped_at == "## two"


def test_a_heading_closed_with_hashes_is_matched_as_it_stands():
    """``## A ##`` — тоже заголовок, но искать его надо той же строкой: сравнение идёт целиком,
    и ``## A`` его не найдёт."""
    edited, _ = body.op_set_section("## A ##\nx\n## B\ny", heading="## A ##", text="Z")
    assert edited == "Z\n## B\ny"

    with pytest.raises(ValueError, match="not found"):
        body.op_set_section("## A ##\nx\n## B\ny", heading="## A", text="Z")


def test_a_hash_without_a_space_is_not_a_heading():
    with pytest.raises(ValueError, match="not a markdown heading"):
        body.op_set_section("#hashtag\nx", heading="#hashtag", text="z")


def test_a_setext_heading_neither_names_a_section_nor_ends_one():
    """Принятое ограничение: подчёркнутый заголовок (``===``) редактор заголовком не считает.
    Назвать им раздел нельзя, и — что важнее — он не обрывает раздел выше: вырез проезжает
    сквозь него до конца тела."""
    with pytest.raises(ValueError, match="not a markdown heading"):
        body.op_set_section("Title\n=====\nx", heading="Title", text="z")

    _, cut = body.op_set_section("# A\nx\nSetext\n======\ny", heading="# A", text="Z")

    assert cut.stopped_at is None
    assert cut.removed == "# A\nx\nSetext\n======\ny"


# ── фенсы ────────────────────────────────────────────────────────────────────
def test_an_unclosed_fence_hides_every_heading_below_it():
    """Принятое ограничение: фенс без закрытия глушит заголовки до конца тела — раздел под ним
    не найти вовсе."""
    with pytest.raises(ValueError, match="not found"):
        body.op_set_section("## A\n```\ncode\n## B\ny", heading="## B", text="Z")


def test_a_section_holding_an_unclosed_fence_runs_to_the_end_of_the_body():
    _, cut = body.op_set_section("## A\n```\ncode\n## B\ny", heading="## A", text="Z")

    assert cut.stopped_at is None
    assert cut.removed_length == len("## A\n```\ncode\n## B\ny")


def test_a_shorter_fence_does_not_close_a_longer_one():
    """Вложенные фенсы: внутренний ``` не закрывает внешний ````, поэтому заголовок внутри
    остаётся кодом, а раздел не обрывается на нём."""
    src = "## A\n````\n```\n# inner\n```\n````\ntail\n## B\nb"

    edited, cut = body.op_set_section(src, heading="## A", text="Z")

    assert edited == "Z\n## B\nb"
    assert cut.removed.endswith("tail")


def test_a_tilde_fence_does_not_close_a_backtick_one():
    src = "## A\n```\n~~~\n# x\n~~~\n```\n## B\nb"

    edited, _ = body.op_set_section(src, heading="## A", text="Z")

    assert edited == "Z\n## B\nb"


def test_a_fence_that_carries_a_language_does_not_close_anything():
    src = "## A\n```\n```python\n# x\n```\ntail\n## B\nb"

    _, cut = body.op_set_section(src, heading="## A", text="Z")

    assert cut.removed.endswith("tail")


# ── переносы строк ───────────────────────────────────────────────────────────
def test_a_crlf_body_is_cut_at_the_right_heading():
    """CRLF приезжает из редакторов пользователя и через фикстуру не воспроизводится — только
    юнитом. Границу раздела ``\\r`` не сбивает: заголовок сравнивается после ``strip``."""
    edited, cut = body.op_set_section("## A\r\nx\r\n## B\r\ny", heading="## A", text="## A2")

    assert cut.stopped_at == "## B"
    assert edited == "## A2\n## B\r\ny"


def test_a_crlf_fence_still_hides_the_heading_inside_it():
    _, cut = body.op_set_section(
        "## A\r\n```\r\n# not a heading\r\n```\r\ntail\r\n## B\r\nb", heading="## A", text="Z"
    )

    assert cut.stopped_at == "## B"
    assert "# not a heading" in cut.removed


def test_a_crlf_body_loses_the_carriage_return_of_the_lines_the_edit_rewrites():
    """Принятое ограничение: сплайс собирает тело через ``\\n``, поэтому вписанный текст едет с
    LF, а нетронутые строки сохраняют CRLF — тело становится смешанным."""
    edited, _ = body.op_set_section("# A\r\nx\r\n# B\r\ny", heading="# A", text="# A2\r\nnew")

    assert edited == "# A2\r\nnew\n# B\r\ny"


# ── пути ─────────────────────────────────────────────────────────────────────
def test_a_path_whose_segments_do_not_nest_is_refused_naming_the_parent():
    """Сегменты, каждый из которых в теле есть, но в обратном порядке: второй ищется внутри
    блока первого, и отказ называет, где именно его не нашли."""
    with pytest.raises(ValueError, match=r"not found inside '### B'"):
        body.op_set_section("## A\nx\n### B\ny", heading="### B > ## A", text="z")


def test_a_path_segment_outside_its_parents_block_is_refused():
    with pytest.raises(ValueError, match=r"'# C' not found inside '## D'"):
        body.op_set_section("# A\n## B\nb\n# C\n## D\nd", heading="## D > # C", text="z")


# ── замена ───────────────────────────────────────────────────────────────────
def test_a_replacement_containing_the_find_is_not_replaced_again():
    """Замена идёт по исходному телу, а не по результату: ``X`` → ``XX`` не запускает себя
    заново."""
    assert body.op_replace("aXa", find="X", text="XX") == ("aXXa", [f"a{PLACEHOLDER}a"])
    assert body.op_replace_all("a a", find="a", text="aa")[0] == "aa aa"


def test_overlapping_occurrences_count_as_one():
    """``aa`` в ``aaa`` — одно вхождение, а не два: перекрытия не считаются, поэтому режим
    ``single`` тут не отказывает, а меняет левое."""
    assert body.op_replace("aaa", find="aa", text="b") == ("ba", [f"{PLACEHOLDER}a"])
    assert body.op_replace_all("aaa", find="aa", text="b")[0] == "ba"


# ── вырожденные тела ─────────────────────────────────────────────────────────
def test_an_empty_body_has_no_sections():
    with pytest.raises(ValueError, match="not found in the body"):
        body.op_set_section("", heading="# A", text="x")


def test_a_body_that_is_only_a_heading_is_cut_whole():
    edited, cut = body.op_set_section("# A", heading="# A", text="")

    assert edited == ""
    assert cut.removed == "# A" and cut.stopped_at is None


def test_a_one_line_body_without_a_trailing_newline_gets_the_text_glued_on():
    """Разделителя тул не добавляет — обещано в описании, и шов показывает именно стык."""
    assert body.op_append("line", text="tail", position="end") == ("linetail", f"line{PLACEHOLDER}")


def test_removing_a_section_with_an_empty_text_leaves_a_blank_line():
    """``text=""`` — это одна пустая строка, а не ноль строк: сплайс дословный, и на месте
    выреза остаётся пустая строка."""
    edited, _ = body.op_set_section("# A\nx\n# B\ny", heading="# A", text="")

    assert edited == "\n# B\ny"


def test_an_empty_anchor_is_unique_in_an_empty_body():
    """Пустой якорь в пустом теле встречается ровно один раз (семантика ``str``), и вставка
    проходит — отказывать тут не за что, тело и так пустое."""
    assert body.op_insert("", text="T", anchor="", position="before") == ("T", PLACEHOLDER)


# ── окно шва ─────────────────────────────────────────────────────────────────
def test_a_window_filled_exactly_to_the_promised_size_carries_no_truncation_mark():
    _, seam = body.op_append("z" * PROMISED_WINDOW, text="A", position="end")

    assert seam == f"{'z' * PROMISED_WINDOW}{PLACEHOLDER}"


def test_one_character_over_the_window_starts_being_marked():
    _, seam = body.op_append("z" * (PROMISED_WINDOW + 1), text="A", position="end")

    assert seam == f"…{'z' * PROMISED_WINDOW}{PLACEHOLDER}"


def test_a_body_shorter_than_the_window_comes_whole_on_both_sides():
    _, seam = body.op_insert("ab|cd", text="_", anchor="|", position="after")

    assert seam == f"ab|{PLACEHOLDER}cd"
