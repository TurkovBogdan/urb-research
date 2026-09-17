"""Перенос исследования между установками: формат ``.urch``, экспорт и импорт.

Архив несёт всю цепочку — исследование, его области и заметки, источниковые запросы, прогоны
поиска с выдачей, источники и материал страниц, — поэтому перенос по построению пересекает
границу модулей: свои таблицы research пишет сам, чужие отдаёт шву ``web_search.services.transfer``.

Снаружи нужны три вещи: ``export_research`` (собрать архив), ``analyze_archive`` (сказать, что
произойдёт с базой) и ``import_archive`` (сделать это). Остальное — внутренности формата.
"""

from src.modules.research.transfer.errors import ArchiveError
from src.modules.research.transfer.export import ExportedArchive, export_research
from src.modules.research.transfer.ingest import ImportReport
from src.modules.research.transfer.plan import ImportPlan
from src.modules.research.transfer.runner import analyze_archive, import_archive

__all__ = [
    "ArchiveError",
    "ExportedArchive",
    "ImportPlan",
    "ImportReport",
    "analyze_archive",
    "export_research",
    "import_archive",
]
