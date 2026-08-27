"""Повтор получения материала источников — общий шаг MCP-тула и HTTP-ручек.

Источник материалом не владеет: он ссылается на страницу ``web_search``, дедуплицированную по
url между исследованиями. Поэтому качаем по **страницам**, а статусы приводим в порядок двумя
разными правилами: у запрошенных источников статус пересобирается по странице (вердикт
снимается — он был вынесен по прежнему материалу), у их соседей по той же странице снимается
только ``error``, разбор соседа не наш.

Выключенный движок контента поднимается из ``Searcher.refetch`` как ``RuntimeError`` — до сети
и до правки статусов; формулировку отказа выбирает вызывающий (тул/ручка).
"""

from __future__ import annotations

from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud.source_document import SourceDocumentWithPage
from src.modules.web_search.services.searcher import Searcher


async def refetch_sources(
    documents: list[SourceDocumentWithPage],
) -> list[SourceDocumentWithPage]:
    """Перекачать страницы переданных источников; вернуть их свежие строки (пустой вход — пустой выход)."""
    if not documents:
        return []
    codes = [doc.code for doc, _ in documents]
    page_codes = list({doc.page_code for doc, _ in documents})
    await Searcher.refetch(page_codes)
    await source_document_crud.source_document_revive_by_pages(page_codes)
    await source_document_crud.source_document_reset_by_codes(codes)
    return await source_document_crud.source_document_list_by_codes(codes)


__all__ = ["refetch_sources"]
