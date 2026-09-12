"""research: границы текстовых полей — ровно на лимите, на символ ниже и на символ выше.

Размер поля в этом модуле — не ошибка валидации, а усечение в CRUD (``_clip``), и режет оно по
**code points**. Значит, у границы есть два вопроса: попадает ли она туда, куда обещана
(96 / 512 / 1024), и что случается с символом, который состоит из нескольких code points.
Ответы на второй — принятые ограничения, и они тут зафиксированы как есть.

Пустая строка, пробелы и опущенное поле — третий вопрос: у них три разных смысла, и путать их
нельзя (``""`` = стереть, отсутствие = не трогать).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.db

# Лимиты — литералами: они обещаны агенту в описании каждого тула («up to 96 chars», «≤1024»),
# и разъезд описания с кодом это и есть поломка, а не подробность реализации.
TITLE = 96
DESCRIPTION = 512
BRIEF = 1024


async def _research(call) -> str:
    return (await call("research_create", title="R"))["code"]


async def _created_field(call, tool: str, field: str, value: str, reader: str, key: str) -> str:
    """Создать сущность с одним заполненным полем и вернуть, как оно сохранилось."""
    parent = {}
    if tool in ("area_create", "note_create"):
        parent["research_code"] = await _research(call)
    if tool == "note_create":
        parent["kind"] = "idea"
    fields = {"title": "T", **parent, field: value}
    code = (await call(tool, **fields))["code"]
    return (await call(reader, **{key: code}))[field]


# (тул создания, поле, лимит, тул чтения, имя аргумента кода)
FIELD_CASES = [
    ("research_create", "title", TITLE, "research_get", "research_code"),
    ("research_create", "description", DESCRIPTION, "research_get", "research_code"),
    ("area_create", "title", TITLE, "area_get", "area_code"),
    ("area_create", "description", DESCRIPTION, "area_get", "area_code"),
    ("area_create", "objective", BRIEF, "area_get", "area_code"),
    ("area_create", "scope", BRIEF, "area_get", "area_code"),
    ("area_create", "expectations", BRIEF, "area_get", "area_code"),
    ("note_create", "title", TITLE, "note_get", "note_code"),
    ("note_create", "description", DESCRIPTION, "note_get", "note_code"),
    ("group_create", "title", TITLE, "group_get", "group_code"),
    ("group_create", "description", DESCRIPTION, "group_get", "group_code"),
]
FIELD_IDS = [f"{tool}-{field}" for tool, field, *_ in FIELD_CASES]


@pytest.mark.parametrize("tool,field,limit,reader,key", FIELD_CASES, ids=FIELD_IDS)
async def test_a_field_one_short_of_its_limit_is_kept_whole(call, tool, field, limit, reader, key):
    value = "щ" * (limit - 1)

    assert await _created_field(call, tool, field, value, reader, key) == value


@pytest.mark.parametrize("tool,field,limit,reader,key", FIELD_CASES, ids=FIELD_IDS)
async def test_a_field_exactly_at_its_limit_is_kept_whole(call, tool, field, limit, reader, key):
    value = "щ" * limit

    assert await _created_field(call, tool, field, value, reader, key) == value


@pytest.mark.parametrize("tool,field,limit,reader,key", FIELD_CASES, ids=FIELD_IDS)
async def test_a_field_one_over_its_limit_loses_exactly_one_character(
    call, tool, field, limit, reader, key
):
    value = "щ" * limit + "Ω"

    stored = await _created_field(call, tool, field, value, reader, key)

    assert stored == "щ" * limit
    assert "Ω" not in stored


async def test_the_brief_is_wider_than_the_description(call):
    """Бриф области и её описание — разные лимиты; спутав их, усечение резало бы план области
    по мерке строки списка."""
    research = await _research(call)
    long_text = "b" * BRIEF
    code = (
        await call(
            "area_create",
            research_code=research,
            title="A",
            description=long_text,
            objective=long_text,
        )
    )["code"]

    row = await call("area_get", area_code=code)

    assert len(row["description"]) == 512
    assert len(row["objective"]) == 1024


async def test_clipping_counts_code_points_not_bytes(call):
    """96 эмодзи — это 96 символов и 384 байта; режется по символам, иначе заголовок терялся бы
    втрое раньше обещанного."""
    title = "🙂" * TITLE

    stored = await _created_field(
        call, "research_create", "title", title, "research_get", "research_code"
    )

    assert stored == title
    assert len(stored.encode("utf-8")) == 384


async def test_clipping_can_split_a_combining_pair(call):
    """Принятое ограничение: граница считает code points, поэтому диакритика, стоящая 97-м
    символом, отваливается — буква остаётся, ударение нет."""
    title = "a" * (TITLE - 1) + "e" + "́"

    stored = await _created_field(
        call, "research_create", "title", title, "research_get", "research_code"
    )

    assert len(stored) == 96
    assert stored.endswith("e")
    assert "́" not in stored


async def test_clipping_can_split_an_emoji_family(call):
    """То же ограничение в самой заметной форме: склейка из нескольких code points режется
    посередине, и в заголовке остаётся висящий zero-width joiner."""
    family = "\U0001f468‍\U0001f469‍\U0001f467"
    title = "x" * (TITLE - 2) + family

    stored = await _created_field(
        call, "research_create", "title", title, "research_get", "research_code"
    )

    assert len(stored) == 96
    assert stored.endswith("\U0001f468‍")


async def test_direction_marks_survive_the_round_trip(call):
    """RTL-переключатели — обычные символы текста: ни усечения, ни чистки их не касаются."""
    title = "‮abc‬"

    stored = await _created_field(
        call, "research_create", "title", title, "research_get", "research_code"
    )

    assert stored == title


async def test_a_whitespace_title_is_stored_as_it_came(call):
    """Пробелы не схлопываются и не превращаются в пустую строку: тул ничего не нормализует."""
    stored = await _created_field(
        call, "research_create", "title", "   ", "research_get", "research_code"
    )

    assert stored == "   "


async def test_an_omitted_description_becomes_an_empty_string(call):
    """Колонка не nullable: не переданное описание — ``""``, а не ``null``; агент читает пустое
    поле, а не отсутствующее."""
    code = (await call("research_create", title="R"))["code"]

    assert (await call("research_get", research_code=code))["description"] == ""


async def _described_entity(call, kind: str) -> tuple[str, str]:
    """Сущность с заполненным описанием → (тул правки, аргумент кода) и сам код в нём."""
    if kind == "research":
        return "research_code", (await call("research_create", title="T", description="d"))["code"]
    if kind == "group":
        return "group_code", (await call("group_create", title="T", description="d"))["code"]
    research = await _research(call)
    if kind == "area":
        created = await call("area_create", research_code=research, title="T", description="d")
        return "area_code", created["code"]
    created = await call(
        "note_create", research_code=research, kind="idea", title="T", description="d"
    )
    return "note_code", created["code"]


@pytest.mark.parametrize("kind", ["research", "area", "note", "group"])
async def test_an_empty_string_blanks_a_field_while_omitting_it_keeps_it(call, kind):
    """Два разных смысла одного аргумента: ``""`` стирает, отсутствие сохраняет. Спутав их,
    правка заголовка стирала бы описание."""
    key, code = await _described_entity(call, kind)
    update = f"{kind}_update"

    kept = await call(update, **{key: code, "title": "T2"})
    assert kept["description"] == "d"

    blanked = await call(update, **{key: code, "description": ""})
    assert blanked["description"] == ""
    assert blanked["title"] == "T2"


async def test_a_body_carries_no_limit(call):
    """Тело — не строка списка: лимита у него нет ни у одной из трёх сущностей с телом."""
    research = await _research(call)
    area = (await call("area_create", research_code=research, title="A"))["code"]
    note = (await call("note_create", research_code=research, kind="idea", title="N"))["code"]
    long_body = "я" * (BRIEF * 4)

    for code, reader, key in (
        (research, "research_get", "research_code"),
        (area, "area_get", "area_code"),
        (note, "note_get", "note_code"),
    ):
        await call("body_set", code=code, text=long_body)
        assert (await call(reader, **{key: code}))["body"] == long_body


async def test_a_body_keeps_crlf_line_endings_verbatim(call):
    """CRLF приезжает из редактора пользователя и хранится как есть: ни нормализации, ни
    потери ``\\r`` при сохранении."""
    code = await _research(call)
    body = "# Заголовок\r\n\r\nтекст\r\n"

    receipt = await call("body_set", code=code, text=body)

    assert receipt["length"] == len(body)
    assert (await call("research_get", research_code=code))["body"] == body
