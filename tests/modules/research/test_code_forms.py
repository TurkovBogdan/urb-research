"""research MCP: формы кода на входе — длина, регистр, тип-слово, его отсутствие.

``test_codes`` пинует сам кодек (снятый формат, голый код), ``test_delete`` — диспетч удаления.
Здесь — то, что видно только с поверхности: какие формы тулы принимают молча, какие отвергают и
чем именно отвечают. Отказ тут — рабочий инструмент: код приезжает из транскрипта, и «не найдено»
на код неправильной формы ничему агента не учит.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db

# Длина кода — литералом: 10 знаков обещаны агенту в тексте отказа, и это часть контракта.
HASH = "0" * 10
RETIRED = "b" * 22


async def _research(call) -> str:
    return (await call("research_create", title="R"))["code"]


@pytest.mark.parametrize("length", [9, 11], ids=["one-short", "one-long"])
async def test_a_code_of_the_wrong_length_is_just_not_found(call, length):
    """Отказ, объясняющий формат, положен ровно снятому 22-значному коду. Код на знак короче или
    длиннее — не «формат», а просто промах: такой код не выдавала ни одна версия."""
    with pytest.raises(ToolError, match="not found"):
        await call("research_get", research_code="RESEARCH@" + "a" * length)


async def test_an_uppercase_tail_is_not_the_retired_format(call):
    """Отказ снятому формату смотрит на алфавит: hex в верхнем регистре кодом не был никогда,
    и накрывать его объяснением про 22 знака значило бы врать о причине."""
    with pytest.raises(ToolError, match="not found"):
        await call("research_get", research_code="RESEARCH@" + "B" * 22)


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("research_get", {"research_code": f"RESEARCH@{RETIRED}"}),
        ("areas_list", {"research_code": f"RESEARCH@{RETIRED}"}),
        ("area_get", {"area_code": f"AREA@{RETIRED}"}),
        ("note_get", {"note_code": f"NOTE@{RETIRED}"}),
        ("group_get", {"group_code": f"GROUP@{RETIRED}"}),
        ("sources_list", {"code": f"AREA@{RETIRED}"}),
        ("source_get", {"source_code": f"SOURCE@{RETIRED}"}),
        ("query_search_list", {"code": f"AREA@{RETIRED}"}),
        ("delete", {"code": f"NOTE@{RETIRED}"}),
        ("interface_open", {"code": f"AREA@{RETIRED}"}),
    ],
    ids=lambda value: value if isinstance(value, str) else "",
)
async def test_the_retired_format_is_answered_the_same_way_everywhere(call, tool, args):
    """Один ответ на всю поверхность: код из старого транскрипта не должен выглядеть как
    «сущность удалили» на одном туле и как «формат снят» на другом."""
    with pytest.raises(ToolError, match="retired 22-char format"):
        await call(tool, **args)


async def test_a_single_type_read_takes_the_code_bare_and_answers_with_it_tagged(call):
    """Снятие префикса идемпотентно, поэтому чтение принимает и голый хеш: тул однотипный, тип
    ему сообщать нечем. Обратно код всё равно едет с тип-словом."""
    code = await _research(call)
    bare = code.removeprefix("RESEARCH@")
    area = await call("area_create", research_code=bare, title="A")

    assert (await call("research_get", research_code=bare))["code"] == code
    assert [row["code"] for row in (await call("areas_list", research_code=bare))["result"]] == [
        area["code"]
    ]


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("delete", {"code": HASH}),
        ("sources_list", {"code": HASH}),
        ("query_search_list", {"code": HASH}),
        ("interface_open", {"code": HASH}),
    ],
    ids=["delete", "sources_list", "query_search_list", "interface_open"],
)
async def test_a_tool_that_dispatches_on_the_type_refuses_a_bare_code(call, tool, args):
    """Обратная половина: где тип-слово выбирает сущность, голый код — не сокращение, а
    неизвестно что, и отказ называет пригодные формы."""
    with pytest.raises(ToolError, match="@"):
        await call(tool, **args)


@pytest.mark.parametrize(
    "prefix", ["RESEARCH", "AREA", "QUERY", "NOTE", "GROUP"]
)
async def test_every_deletable_type_answers_false_for_a_code_that_is_gone(call, prefix):
    """Удаление несуществующего — не ошибка, а ``false``: агент, повторивший вызов, должен
    увидеть «уже нет», а не отказ."""
    assert (await call("delete", code=f"{prefix}@{HASH}"))["result"] is False


async def test_a_type_word_without_a_hash_deletes_nothing(call):
    """``RESEARCH@`` без хвоста — код, которого не бывает; тул отвечает как на любой промах."""
    assert (await call("delete", code="RESEARCH@"))["result"] is False


@pytest.mark.parametrize("code", [f"QUERY@{HASH}", f"GROUP@{HASH}", f"SEARCH@{HASH}", HASH])
async def test_the_body_editor_names_the_three_types_that_have_a_body(call, code):
    with pytest.raises(ToolError, match=r"RESEARCH@ / AREA@ / NOTE@"):
        await call("body_set", code=code, text="x")


async def test_the_type_word_is_case_sensitive(call):
    """Код возвращает сервер, и назад он должен приехать таким же: строчный ``research@`` — не
    код, и лучше отказ, объясняющий типы, чем молчаливое «не найдено»."""
    code = await _research(call)

    with pytest.raises(ToolError, match="not supported"):
        await call("body_set", code=code.lower(), text="x")


async def test_refetch_treats_a_retired_code_as_a_fruitless_one(call):
    """Пакетный тул не роняет вызов из-за одного кода — даже из-за кода снятого формата: пять
    остальных должны доработать, а промах уезжает в отчёт."""
    report = await call("sources_refetch", codes=[f"SOURCE@{RETIRED}", f"NOTE@{HASH}"])

    assert report["sources"] == []
    assert report["skipped"] == [
        {"code": f"SOURCE@{RETIRED}", "reason": "not_found"},
        {"code": f"NOTE@{HASH}", "reason": "not_a_source_code"},
    ]


async def test_refetch_calls_a_bare_code_not_a_source_code(call):
    report = await call("sources_refetch", codes=[HASH])

    assert report["skipped"] == [{"code": HASH, "reason": "not_a_source_code"}]


async def test_refetch_reports_a_repeated_code_once(call):
    """Дубликаты в списке схлопываются до вызова: один код — одна строка отчёта, иначе агент
    считал бы по ней количество пропущенных источников неверно."""
    report = await call("sources_refetch", codes=[f"NOTE@{HASH}", f"NOTE@{HASH}"])

    assert report["skipped"] == [{"code": f"NOTE@{HASH}", "reason": "not_a_source_code"}]


async def test_the_cap_counts_codes_as_they_came_not_after_deduplication(call):
    """Потолок в шесть — про размер ввода, а не про работу после схлопывания: семь одинаковых
    кодов всё равно отказ. Так агент видит правило, которое сам может проверить до вызова."""
    with pytest.raises(ToolError, match="At most 6 codes"):
        await call("sources_refetch", codes=[f"NOTE@{HASH}"] * 7)
