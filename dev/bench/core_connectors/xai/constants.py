"""Константы бенча xAI: директория артефактов + фикс-запросы."""

from __future__ import annotations

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "tmp"

SEARCH_QUERY = "Что нового анонсировала xAI за последний месяц? Кратко, по пунктам."
