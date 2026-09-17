"""Две фазы импорта снаружи: разбор без записи и применение по свежему плану.

Разбор физически не умеет писать в базу — это другая функция, и обещание «до кнопки база не
меняется» держится строением, а не дисциплиной. Применение строит план заново, а не берёт
сохранённый: карта выводится детерминированно и получается той же, зато состояние базы
перечитывается — между двумя запросами человек думал, а агент мог писать.
"""

from __future__ import annotations

from pathlib import Path

from src.modules.research.transfer.archive import ArchiveReader, check_total_size
from src.modules.research.transfer.export import install_id
from src.modules.research.transfer.ingest import ImportReport, apply_plan
from src.modules.research.transfer.plan import ImportPlan, build_plan


async def analyze_archive(path: Path, *, mode: str) -> ImportPlan:
    """Прочитать архив и сказать, что произойдёт с базой."""
    check_total_size(path)
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        reader.verify_inventory()
        return await build_plan(reader, mode=mode, install=await install_id())


async def import_archive(path: Path, *, mode: str) -> tuple[ImportPlan, ImportReport]:
    """Разобрать и применить: план строится заново, поверх текущего состояния базы."""
    check_total_size(path)
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        reader.verify_inventory()
        plan = await build_plan(reader, mode=mode, install=await install_id())
        return plan, await apply_plan(reader, plan)


__all__ = ["analyze_archive", "import_archive"]
