"""Тесты TaskRegistry: регистрация, дубль, get/all (чистая логика, без БД)."""

from __future__ import annotations

import pytest

from src.core.scheduler.registry import TaskRegistry


async def _noop(ctx):  # pragma: no cover - заглушка
    pass


def _kwargs(**overrides):
    base = dict(
        module="m",
        code="c",
        name="Demo",
        description="demo task",
        schedule="* * * * *",
        handler=_noop,
        ttl=60,
        enabled=True,
    )
    base.update(overrides)
    return base


@pytest.mark.pure
def test_register_stores_entry_with_all_fields():
    reg = TaskRegistry()
    reg.register(**_kwargs(schedule="*/5 * * * *", ttl=300))
    entry = reg.get("m", "c")
    assert entry is not None
    assert entry.module == "m"
    assert entry.code == "c"
    assert entry.name == "Demo"
    assert entry.description == "demo task"
    assert entry.schedule == "*/5 * * * *"
    assert entry.handler is _noop
    assert entry.ttl == 300
    assert entry.enabled is True


@pytest.mark.pure
def test_register_duplicate_raises():
    reg = TaskRegistry()
    reg.register(**_kwargs())
    with pytest.raises(ValueError, match="already registered"):
        reg.register(**_kwargs())


@pytest.mark.pure
def test_get_missing_returns_none():
    reg = TaskRegistry()
    assert reg.get("m", "c") is None


@pytest.mark.pure
def test_all_lists_every_entry_in_insertion_order():
    reg = TaskRegistry()
    reg.register(**_kwargs(module="a", code="1"))
    reg.register(**_kwargs(module="b", code="2"))
    entries = reg.all()
    assert [(e.module, e.code) for e in entries] == [("a", "1"), ("b", "2")]


@pytest.mark.pure
def test_same_code_different_module_coexist():
    reg = TaskRegistry()
    reg.register(**_kwargs(module="a", code="x"))
    reg.register(**_kwargs(module="b", code="x"))
    assert reg.get("a", "x") is not None
    assert reg.get("b", "x") is not None
    assert len(reg.all()) == 2
