"""Пределы и канал логов модуля core_interface."""

from __future__ import annotations

LOG_CHANNEL = "core_interface"

# Совпадает с колонкой ``core_interface_settings.key``: слишком длинный ключ должен
# отвергаться проверкой реестра, а не падать на вставке в Postgres (SQLite длину
# игнорирует, поэтому в dev дефект был бы не виден).
KEY_MAX_LENGTH = 128

VALUE_MAX_BYTES = 4096

__all__ = ["LOG_CHANNEL", "KEY_MAX_LENGTH", "VALUE_MAX_BYTES"]
