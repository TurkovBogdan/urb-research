"""build_modules: состав списка модулей приложения."""

from __future__ import annotations

import pytest

from src.apps.app.modules import build_modules
from src.core.module import Module


@pytest.mark.pure
def test_core_setup_is_wired():
    names = [m.name for m in build_modules()]
    assert "core_setup" in names


@pytest.mark.pure
def test_all_entries_are_modules_with_unique_names():
    modules = build_modules()
    assert all(isinstance(m, Module) for m in modules)
    names = [m.name for m in modules]
    assert len(names) == len(set(names))
