"""CRUD-функции ядра. Все обновления — точечные UPDATE по id/key."""

from src.core.crud import lock, tasks, tasks_logs

__all__ = ["lock", "tasks", "tasks_logs"]
