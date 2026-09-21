"""Повтор получения материала источников — общий шаг MCP-тула и HTTP-ручек.

Источник материалом не владеет: он ссылается на страницу ``web_search``, дедуплицированную по
url между исследованиями. Поэтому качаем по **страницам**, а статусы приводим в порядок двумя
разными правилами: у запрошенных источников статус пересобирается по странице (вердикт
снимается — он был вынесен по прежнему материалу), у их соседей по той же странице снимается
только ``error``, разбор соседа не наш.

Выключенный движок контента поднимается из ``Searcher.refetch`` как ``RuntimeError`` — до сети
и до правки статусов; формулировку отказа выбирает вызывающий (тул/ручка).

Тут же ``plan_unfetched`` — что предстоит перекачать: те же источники, свёрнутые до страниц,
потому что работа считается страницами.
"""

from __future__ import annotations

from collections import Counter
from typing import NamedTuple

from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud.source_document import SourceDocumentWithPage
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.services.searcher import Searcher


class UnfetchedPage(NamedTuple):
    """Страница без материала и сколько источников уровня её ждут.

    ``document`` — один из этих источников: просят повтор по источнику, а качается страница.
    """

    document: ResearchSourceDocument
    page: WebSearchPage | None
    sources: int


def plan_unfetched(documents: list[SourceDocumentWithPage]) -> list[UnfetchedPage]:
    """Свернуть источники без материала до страниц — единиц работы.

    Одна страница дедуплицирована между исследованиями и внутри одного: без свёртки заказчик
    повтора разложил бы её по двум разным кускам и скачал дважды.
    """
    representatives: dict[str, SourceDocumentWithPage] = {}
    waiting_sources: Counter[str] = Counter()
    for doc, page in documents:
        representatives.setdefault(doc.page_code, (doc, page))
        waiting_sources[doc.page_code] += 1
    return [
        UnfetchedPage(doc, page, waiting_sources[page_code])
        for page_code, (doc, page) in representatives.items()
    ]


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


__all__ = ["UnfetchedPage", "plan_unfetched", "refetch_sources"]
