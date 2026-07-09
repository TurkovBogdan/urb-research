"""Тесты ticker.is_due (чистая логика, без БД)."""

from __future__ import annotations

import pytest

from datetime import datetime

from src.core.scheduler.ticker import is_due


def _t(year=2026, month=5, day=4, hour=12, minute=0, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second)


@pytest.mark.pure
def test_due_when_no_previous_run():
    assert is_due("*/5 * * * *", _t(), None) is True


@pytest.mark.pure
def test_not_due_before_next_tick():
    last = _t(hour=12, minute=0)
    now = _t(hour=12, minute=3)
    assert is_due("*/5 * * * *", now, last) is False


@pytest.mark.pure
def test_due_at_or_after_next_tick():
    last = _t(hour=12, minute=0)
    now = _t(hour=12, minute=5)
    assert is_due("*/5 * * * *", now, last) is True


@pytest.mark.pure
def test_due_far_after_next_tick():
    last = _t(hour=12, minute=0)
    now = _t(hour=13, minute=0)
    assert is_due("*/5 * * * *", now, last) is True
