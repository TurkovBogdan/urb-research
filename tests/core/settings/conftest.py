"""Фикстура: чистый settings-registry между тестами этой подсистемы."""

from __future__ import annotations

import pytest

from src.core.settings.registry import get_registry


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()
