"""Аксессор к произвольному состоянию модуля (``core_modules_state``).

``module_store(code)`` отдаёт ``ModuleStore`` с предзашитым кодом модуля, чтобы
не таскать ``module=`` в каждый вызов:

    store = module_store("mail_sync")
    await store.set("gmail_import_cursor", {"history_id": "98213"})
    cursor = await store.get("gmail_import_cursor")   # -> dict | None

Тонкая обёртка над ``crud/module_state.py``; место для внутреннего runtime-состояния
(курсоры, счётчики, маркеры), а не пользовательского конфига (тот — в settings).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.crud import module_state as crud


@dataclass(frozen=True)
class ModuleStore:
    """Хранилище состояния одного модуля. Код модуля привязан к экземпляру."""

    module: str

    async def get(self, code: str, default: Any = None) -> Any:
        row = await crud.get_one(self.module, code)
        return row.value if row is not None else default

    async def set(self, code: str, value: Any) -> None:
        await crud.upsert(self.module, code, value)

    async def seed_if_absent(self, code: str, value: Any) -> bool:
        return await crud.seed_if_absent(self.module, code, value)

    async def delete(self, code: str) -> None:
        await crud.delete(self.module, code)

    async def all(self) -> dict[str, Any]:
        rows = await crud.list_for_module(self.module)
        return {row.code: row.value for row in rows}


def module_store(module: str) -> ModuleStore:
    return ModuleStore(module=module)


__all__ = ["ModuleStore", "module_store"]
