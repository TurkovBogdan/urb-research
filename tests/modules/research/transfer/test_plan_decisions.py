"""Арифметика плана импорта: решение по записи, свод и карта ссылок — без базы.

Сам `build_plan` ходит в базу и живёт в `db`-ярусе; здесь проверяется то, что считается из
готовых данных: какое решение принимается по опознанной записи, как решения складываются в свод
для человека и во что превращается карта подмены кодов.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.modules.research.constants import AREA_CODE_PREFIX, RESEARCH_CODE_PREFIX
from src.modules.research.transfer import plan as plan_module
from src.modules.research.transfer.constants import (
    ACTION_CREATE,
    ACTION_MERGE,
    ACTION_SKIP,
    ACTION_UPDATE,
    ENTITY_AREAS,
    ENTITY_RESEARCH,
    ENTITY_SEARCH_RESULTS,
    IMPORT_MODE_ALWAYS,
    IMPORT_MODE_NEVER,
    IMPORT_MODE_NEWER,
)
from src.modules.research.transfer.manifest import Manifest
from src.modules.research.transfer.plan import Decision, ImportPlan, PlanWarnings

pytestmark = pytest.mark.pure

MOMENT = datetime(2026, 1, 2, 3, 4, 5)
LATER = MOMENT + timedelta(hours=1)
RESEARCH_CODE = "0123456789"
AREA_CODE = "abcdef0123"
RECODED_AREA = "9876543210"


def _manifest() -> Manifest:
    return Manifest(
        format="uroboros.research",
        format_version=1,
        archive_id="01JB0000000000000000000000",
        created_at="2026-01-02 03:04:05",
    )


def _plan(decisions, *, rows=None, result_rows=None) -> ImportPlan:
    return ImportPlan(
        manifest=_manifest(),
        mode=IMPORT_MODE_NEWER,
        same_install=False,
        rows=rows or {},
        decisions=decisions,
        result_rows=result_rows or [],
        reference_map={},
        warnings=PlanWarnings(),
    )


@pytest.mark.parametrize(
    ("mode", "archived", "local", "expected"),
    [
        (IMPORT_MODE_NEVER, LATER, MOMENT, ACTION_SKIP),
        (IMPORT_MODE_ALWAYS, MOMENT, LATER, ACTION_UPDATE),
        (IMPORT_MODE_NEWER, LATER, MOMENT, ACTION_UPDATE),
        (IMPORT_MODE_NEWER, MOMENT, LATER, ACTION_SKIP),
        (IMPORT_MODE_NEWER, MOMENT, MOMENT, ACTION_SKIP),
        (IMPORT_MODE_NEWER, None, MOMENT, ACTION_SKIP),
        (IMPORT_MODE_NEWER, MOMENT, None, ACTION_SKIP),
    ],
    ids=["never", "always", "archive-newer", "local-newer", "same", "no-archived", "no-local"],
)
def test_the_decision_on_a_recognised_record_follows_the_mode(mode, archived, local, expected):
    assert plan_module._decide_existing(mode, archived, local) == expected


def test_a_record_equal_to_the_second_is_not_rewritten():
    """Микросекунды местной записи — не правка: архив несёт секунды, и без округления свой же
    архив переписывал бы запись поверх самой себя на каждом заходе."""
    assert (
        plan_module._decide_existing(IMPORT_MODE_NEWER, MOMENT, MOMENT.replace(microsecond=7))
        == ACTION_SKIP
    )


def test_a_decision_that_keeps_the_code_is_not_a_recode():
    assert not Decision(origin=AREA_CODE, code=AREA_CODE, action=ACTION_CREATE).recoded
    assert Decision(origin=AREA_CODE, code=RECODED_AREA, action=ACTION_CREATE).recoded


def test_the_reference_map_keys_every_decision_by_type_and_origin():
    """Карта ссылок строится из решений целиком, включая записи с уцелевшим кодом: подмена
    «сам в себя» безопасна, а пропуск записи означал бы ссылку, которую никто не проверил."""
    reference_map = plan_module._reference_map(
        {
            ENTITY_RESEARCH: {
                RESEARCH_CODE: Decision(RESEARCH_CODE, RESEARCH_CODE, ACTION_UPDATE)
            },
            ENTITY_AREAS: {AREA_CODE: Decision(AREA_CODE, RECODED_AREA, ACTION_CREATE)},
        }
    )
    assert reference_map == {
        (RESEARCH_CODE_PREFIX, RESEARCH_CODE): RESEARCH_CODE,
        (AREA_CODE_PREFIX, AREA_CODE): RECODED_AREA,
    }


def test_the_summary_counts_actions_and_recodes_per_entity():
    plan = _plan(
        {
            ENTITY_AREAS: {
                "a": Decision("a", "a", ACTION_CREATE),
                "b": Decision("b", RECODED_AREA, ACTION_CREATE),
                "c": Decision("c", "c", ACTION_UPDATE),
                "d": Decision("d", "d", ACTION_SKIP),
            }
        }
    )
    assert plan.counts()[ENTITY_AREAS] == {
        ACTION_CREATE: 2,
        ACTION_UPDATE: 1,
        ACTION_SKIP: 1,
        ACTION_MERGE: 0,
        "recode": 1,
    }


def test_every_entity_shows_up_in_the_summary_even_when_the_archive_is_silent_about_it():
    """Свод читает человек: пустая строка таблицы — ответ, отсутствие строки — вопрос."""
    summary = _plan({}).counts()
    assert summary[ENTITY_AREAS] == {
        ACTION_CREATE: 0,
        ACTION_UPDATE: 0,
        ACTION_SKIP: 0,
        ACTION_MERGE: 0,
        "recode": 0,
    }


def test_search_results_are_counted_as_rows_taken_against_rows_left():
    """У строк выдачи нет ни кода, ни решения: считается разница между приехавшим и отобранным."""
    plan = _plan(
        {},
        rows={ENTITY_SEARCH_RESULTS: [{"n": 1}, {"n": 2}, {"n": 3}]},
        result_rows=[{"n": 1}, {"n": 2}],
    )
    assert plan.counts()[ENTITY_SEARCH_RESULTS] == {
        ACTION_CREATE: 2,
        ACTION_UPDATE: 0,
        ACTION_SKIP: 1,
        ACTION_MERGE: 0,
        "recode": 0,
    }


def test_details_name_the_moved_codes_in_the_form_a_human_reads():
    plan = _plan(
        {
            ENTITY_AREAS: {
                AREA_CODE: Decision(AREA_CODE, RECODED_AREA, ACTION_CREATE, title="Область")
            },
            ENTITY_RESEARCH: {
                RESEARCH_CODE: Decision(
                    RESEARCH_CODE, RESEARCH_CODE, ACTION_UPDATE, title="Исследование"
                )
            },
        }
    )
    assert plan.details()["recoded"] == [
        {
            "entity": ENTITY_AREAS,
            "title": "Область",
            "from": f"{AREA_CODE_PREFIX}@{AREA_CODE}",
            "to": f"{AREA_CODE_PREFIX}@{RECODED_AREA}",
        }
    ]
    assert plan.details()["updating"] == [
        {
            "entity": ENTITY_RESEARCH,
            "title": "Исследование",
            "code": f"{RESEARCH_CODE_PREFIX}@{RESEARCH_CODE}",
        }
    ]


def test_the_root_code_is_the_one_the_record_will_live_under():
    """Человек уходит по коду из отчёта: назвать там исходный код значило бы отправить его в
    чужую запись, если код при импорте переехал."""
    plan = _plan(
        {
            ENTITY_RESEARCH: {
                RESEARCH_CODE: Decision(RESEARCH_CODE, RECODED_AREA, ACTION_CREATE, title="Иссл.")
            }
        }
    )
    assert plan.root_codes() == [
        {"code": f"{RESEARCH_CODE_PREFIX}@{RECODED_AREA}", "title": "Иссл."}
    ]


def _locally_newer(archived: str, local: datetime) -> list[dict[str, str]]:
    warnings = PlanWarnings()
    plan_module._note_locally_newer(
        warnings,
        ENTITY_AREAS,
        AREA_CODE,
        "Область",
        IMPORT_MODE_NEWER,
        ACTION_SKIP,
        {"updated_at": archived},
        local,
    )
    return warnings.locally_newer


def test_a_skip_caused_by_a_newer_local_copy_is_reported():
    assert _locally_newer("2026-01-02 03:04:05", LATER) == [
        {"entity": ENTITY_AREAS, "code": f"{AREA_CODE_PREFIX}@{AREA_CODE}", "title": "Область"}
    ]


@pytest.mark.parametrize(
    ("mode", "action"),
    [
        (IMPORT_MODE_NEVER, ACTION_SKIP),
        (IMPORT_MODE_ALWAYS, ACTION_UPDATE),
        (IMPORT_MODE_NEWER, ACTION_UPDATE),
    ],
    ids=["never", "always", "updating"],
)
def test_a_skip_by_the_operators_own_choice_is_not_reported(mode, action):
    """Предупреждение объясняет неожиданное: пропуск, который человек заказал режимом, — ожидаем."""
    warnings = PlanWarnings()
    plan_module._note_locally_newer(
        warnings, ENTITY_AREAS, AREA_CODE, "Область", mode, action,
        {"updated_at": "2026-01-02 03:04:05"}, LATER,
    )
    assert warnings.locally_newer == []


def test_a_record_the_archive_matches_exactly_is_not_reported():
    assert _locally_newer("2026-01-02 03:04:05", MOMENT) == []


def test_microseconds_alone_do_not_make_the_local_copy_newer():
    """Сводка предупреждений — то, на что человек смотрит перед нажатием кнопки: запись, равная
    архиву с точностью до секунды, попадать в «местная копия свежее» не должна."""
    assert _locally_newer("2026-01-02 03:04:05", MOMENT.replace(microsecond=7)) == []
