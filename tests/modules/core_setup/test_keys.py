"""Форма настроек окружения: как вводятся поля, у которых выбор закрыт."""

from __future__ import annotations

import pytest

from src.modules.core_setup.keys import FIELD_BY_KEY, UPDATE_BRANCHES

pytestmark = pytest.mark.pure


@pytest.mark.parametrize("key", ["DB_PROVIDER", "UPDATE_BRANCH"])
def test_closed_choices_are_entered_by_selection(key: str):
    """`choice` — это VSelect на странице; `str` дал бы свободный ввод там, где вариантов два."""
    assert FIELD_BY_KEY[key].type == "choice"
    assert FIELD_BY_KEY[key].choices


def test_update_branch_offers_the_lines_the_project_keeps():
    """Ветка уходит в аргументы git, и опечатка в ней вскрывается уже после остановки установки."""
    assert FIELD_BY_KEY["UPDATE_BRANCH"].choices == UPDATE_BRANCHES
    assert set(UPDATE_BRANCHES) == {"main", "dev"}
