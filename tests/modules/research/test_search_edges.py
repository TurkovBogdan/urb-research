"""research MCP: края поисково-источниковой части — сбой прогона, фильтр статуса, удалённая родня.

``test_search_sources`` пинует счастливый путь прогона и разбора. Здесь — то, что возвращается
агенту, когда прогон **не состоялся**, когда фильтр списка назван неверно и когда родитель
источников удалён. Общая нить: пустой список значит «ничего нет», и любой другой смысл,
приехавший в этой же форме, агент прочитает как «работа кончена».
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db

HASH = "0" * 10


async def _area(call) -> tuple[str, str]:
    research = (await call("research_create", title="R"))["code"]
    area = (await call("area_create", research_code=research, title="A"))["code"]
    return research, area


async def _run(call, use_search, n: int = 2):
    """research + area + прогон на ``n`` страниц. → (research, area, источники)."""
    use_search(
        results=[{"url": f"https://ex.com/{i}", "rank": i, "summary": f"s{i}"} for i in range(n)],
        pages={f"https://ex.com/{i}": f"# b{i}" for i in range(n)},
    )
    research, area = await _area(call)
    sources = (await call("query_search_run", area_code=area, query="q"))["result"]
    return research, area, sources


# ── дефект: несостоявшийся прогон выглядит как прогон без результатов ────────
async def test_a_search_with_a_disabled_engine_does_not_look_like_an_empty_result(
    call, use_search, monkeypatch
):
    """ДЕФЕКТ: движок поиска выключен — тул отдаёт пустой список, то есть ровно то же, что и
    честный прогон, ничего не нашедший.

    Прогон при этом записан (``query_search_list`` показывает запрос), а web_search пометил его
    ``error``: ``search_engine_disabled``. Агент читает пустой ответ как «по этому запросу нет
    источников», меняет формулировку и идёт дальше — вместо того чтобы сказать пользователю, что
    поиск не работает. Соседний тул той же поверхности так не делает: ``sources_refetch``
    отказывает словами ``fetch_engine_disabled`` до всякой сети.
    """
    engine = use_search(results=[{"url": "https://ex.com/0", "rank": 0, "summary": "s"}])

    async def _not_ready() -> bool:
        return False

    monkeypatch.setattr(engine, "available", _not_ready)
    _, area = await _area(call)

    with pytest.raises(ToolError, match="engine"):
        await call("query_search_run", area_code=area, query="q")


async def test_a_search_whose_engine_failed_does_not_look_like_an_empty_result(
    call, use_search, monkeypatch
):
    """ДЕФЕКТ, та же форма: движок поднял исключение (сеть, ключ, лимит) — прогон помечен
    ``error``, а агенту приехал пустой список без единого признака сбоя."""
    engine = use_search(results=[])

    async def _boom(request):
        raise ConnectionError("search api down")

    monkeypatch.setattr(engine, "search", _boom)
    _, area = await _area(call)

    with pytest.raises(ToolError):
        await call("query_search_run", area_code=area, query="q")


@pytest.mark.parametrize("status", ["pendng", ""], ids=["typo", "empty"])
async def test_sources_list_refuses_a_status_it_does_not_know(call, use_search, status):
    """ДЕФЕКТ: неизвестный статус не отказ, а пустой список — при том что ровно по этому вызову
    агенту велено проверять, не осталось ли неразобранного («sources_list(area_code,
    status='pending') must end empty before you write the synthesis»).

    Опечатка в статусе превращается в «всё разобрано». Пустая строка — та же беда с другой
    стороны: в остальном модуле ``""`` значит «не задано», а тут она фильтрует по статусу ``""``,
    которого не бывает. Соседние тулы проверяют такое же перечисление явно (``notes_list`` —
    ``kind``, ``source_review`` — ``decision``).
    """
    research, _, _ = await _run(call, use_search, n=2)

    with pytest.raises(ToolError, match="pending"):
        await call("sources_list", code=research, status=status)


# ── фильтр статуса, который работает ─────────────────────────────────────────
@pytest.mark.parametrize("status", ["pending", "kept", "filtered", "error"])
async def test_every_documented_status_is_a_usable_filter(call, use_search, status):
    research, _, sources = await _run(call, use_search, n=2)
    await call("source_review", source_code=sources[0]["code"], decision="keep", relevance=9)
    await call(
        "source_review", source_code=sources[1]["code"], decision="filter", relevance=2, note="dup"
    )
    expected = {"pending": 0, "kept": 1, "filtered": 1, "error": 0}[status]

    rows = (await call("sources_list", code=research, status=status))["result"]

    assert len(rows) == expected


# ── разбор ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("relevance", [1, 10])
async def test_the_ends_of_the_relevance_scale_are_accepted(call, use_search, relevance):
    _, _, sources = await _run(call, use_search, n=1)

    reviewed = await call(
        "source_review", source_code=sources[0]["code"], decision="keep", relevance=relevance
    )

    assert reviewed["status"] == "kept"


@pytest.mark.parametrize("relevance", [0, 11, -1])
async def test_a_relevance_outside_the_scale_is_refused(call, use_search, relevance):
    _, _, sources = await _run(call, use_search, n=1)

    with pytest.raises(ToolError, match="relevance must be between 1 and 10"):
        await call(
            "source_review", source_code=sources[0]["code"], decision="keep", relevance=relevance
        )


async def test_a_review_without_a_note_keeps_the_previous_one(call, use_search):
    """``note`` опущен — прежняя причина остаётся: перерешив ``keep`` → ``filter``, агент не
    обязан переписывать заметку, и стирать её молча было бы потерей разбора."""
    research, _, sources = await _run(call, use_search, n=1)
    code = sources[0]["code"]
    await call("source_review", source_code=code, decision="filter", relevance=2, note="дубль")

    await call("source_review", source_code=code, decision="keep", relevance=8)

    row = (await call("sources_list", code=research))["result"][0]
    assert row["note"] == "дубль" and row["relevance"] == 8


# ── перекачка ────────────────────────────────────────────────────────────────
async def test_refetch_leaves_a_source_that_has_its_material_alone(call, use_search):
    """Чинить нечего — это отдельный ответ, а не пустая работа: источник с материалом в отчёт
    ``sources`` не попадает вовсе."""
    _, _, sources = await _run(call, use_search, n=1)

    report = await call("sources_refetch", codes=[sources[0]["code"]])

    assert report["sources"] == []
    assert report["skipped"] == [{"code": sources[0]["code"], "reason": "nothing_to_fix"}]


async def test_refetch_reports_each_kind_of_fruitless_code_in_one_call(call, use_search):
    """Смешанный пакет: три разные причины отказа и один живой код — вызов не падает ни на
    одной из них, и каждая названа своим словом."""
    use_search(results=[{"url": "https://ex.com/0", "rank": 0, "summary": "s"}], pages={})
    research, area = await _area(call)
    broken = (await call("query_search_run", area_code=area, query="q"))["result"]
    healthy_research, _, _ = await _run(call, use_search, n=1)

    report = await call(
        "sources_refetch",
        codes=[f"SOURCE@{HASH}", f"PAGE@{HASH}", healthy_research, research],
    )

    assert [row["reason"] for row in report["skipped"]] == [
        "not_found",
        "not_a_source_code",
        "nothing_to_fix",
    ]
    assert [row["code"] for row in report["sources"]] == [broken[0]["code"]]


async def test_refetch_of_the_exact_number_of_allowed_codes_goes_through(call, use_search):
    """Потолок включительный: шесть кодов — работа, седьмой — отказ (пинуется рядом)."""
    _, _, sources = await _run(call, use_search, n=1)

    report = await call("sources_refetch", codes=[sources[0]["code"]] + [f"NOTE@{HASH}"] * 5)

    assert len(report["skipped"]) == 2


# ── удалённая родня ──────────────────────────────────────────────────────────
async def test_deleting_an_area_takes_its_searches_and_sources_but_not_the_research(
    call, use_search
):
    research, area, _ = await _run(call, use_search, n=2)

    assert (await call("delete", code=area))["result"] is True

    assert (await call("sources_list", code=research))["result"] == []
    assert (await call("query_search_list", code=research))["result"] == []
    assert (await call("research_get", research_code=research))["areas"] == []


async def test_deleting_a_research_takes_the_sources_under_it(call, use_search):
    research, area, sources = await _run(call, use_search, n=2)

    assert (await call("delete", code=research))["result"] is True

    with pytest.raises(ToolError, match="Source .* not found"):
        await call("source_get", source_code=sources[0]["code"])
    with pytest.raises(ToolError, match="Area .* not found"):
        await call("query_search_run", area_code=area, query="q")


async def test_deleting_a_search_run_leaves_the_other_runs_of_the_area(call, use_search):
    _, area, _ = await _run(call, use_search, n=1)
    await call("query_search_run", area_code=area, query="второй")
    runs = (await call("query_search_list", code=area))["result"]

    assert (await call("delete", code=runs[0]["code"]))["result"] is True

    left = (await call("query_search_list", code=area))["result"]
    assert [row["code"] for row in left] == [runs[1]["code"]]
    assert len((await call("sources_list", code=area))["result"]) == 1


async def test_the_same_url_found_twice_in_one_run_becomes_one_source(call, use_search):
    """Страница дедуплицирована по url в web_search, и источник за ней один: иначе агент
    разбирал бы один и тот же материал дважды."""
    use_search(
        results=[
            {"url": "https://ex.com/0", "rank": 0, "summary": "первый"},
            {"url": "https://ex.com/0", "rank": 1, "summary": "второй"},
        ],
        pages={"https://ex.com/0": "# b"},
    )
    _, area = await _area(call)

    found = (await call("query_search_run", area_code=area, query="q"))["result"]

    assert len(found) == 1
