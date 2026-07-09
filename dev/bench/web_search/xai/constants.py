"""Константы верстака xAI (web_search): директория артефактов + фикс-запрос."""

from __future__ import annotations

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "tmp"
TIMEOUT = 120.0

SEARCH_QUERY = "Создание системы очередей на Python"
MAX_RESULTS = 8
