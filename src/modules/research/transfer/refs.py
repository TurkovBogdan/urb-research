"""Перекрёстные ссылки ``TYPE@hash`` в текстах: сбор и подмена по карте импорта.

Тела исследования, областей и заметок ссылаются на сущности кодами, и при импорте с
перевыпуском кода эти ссылки обязаны переехать вместе с записями. Подмена идёт **одним
проходом одной регуляркой** со словарём: замена пара-за-парой сцепляется сама с собой (код,
только что ставший ``B``, второй парой уезжает в ``C``) и портит тела молча.

Ключ словаря — пара «тип + код», а не голый код: один и тот же хеш вправе оказаться кодом
области в архиве и кодом заметки в базе, и подмены у них разные.
"""

from __future__ import annotations

import re

from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    CODE_LEN,
    GROUP_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    PAGE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
    SEARCH_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
)

# Коды web_search (прогон поиска и страница) этой длиной не управляются — они остаются
# 22-символьными (``hashing._HASH_LEN``), и в телах встречаются наравне с research-кодами.
WEB_SEARCH_CODE_LEN = 22

_RESEARCH_PREFIXES = (
    RESEARCH_CODE_PREFIX,
    AREA_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    SOURCE_QUERY_CODE_PREFIX,
    SOURCE_DOCUMENT_CODE_PREFIX,
    GROUP_CODE_PREFIX,
)
_WEB_SEARCH_PREFIXES = (SEARCH_CODE_PREFIX, PAGE_CODE_PREFIX)


def _pattern(prefixes: tuple[str, ...], length: int) -> re.Pattern[str]:
    """Ссылка ``TYPE@hash`` ровно заданной длины.

    Просмотр вперёд отсекает более длинный хеш: без него у 22-символьного кода откусились бы
    первые десять символов и ссылка переехала бы в никуда. Тот же приём — во фронтовом
    ``REF_CODE`` (``web/src/components/markdown/render.ts``).
    """
    return re.compile(rf"\b({'|'.join(prefixes)})@([0-9a-f]{{{length}}})(?![0-9a-f])")


REFERENCE_PATTERNS = (
    _pattern(_RESEARCH_PREFIXES, CODE_LEN),
    _pattern(_WEB_SEARCH_PREFIXES, WEB_SEARCH_CODE_LEN),
)


def collect_references(text: str | None) -> set[tuple[str, str]]:
    """Пары «тип, голый код» из текста — то, на что он ссылается."""
    if not text:
        return set()
    return {
        (match.group(1), match.group(2))
        for pattern in REFERENCE_PATTERNS
        for match in pattern.finditer(text)
    }


def rewrite_references(text: str | None, mapping: dict[tuple[str, str], str]) -> tuple[str | None, int]:
    """Переписать ссылки по карте ``(тип, старый код) → новый код``; вернуть текст и счётчик.

    Каждое вхождение разрешается ровно один раз: результат замены больше не просматривается,
    поэтому цепочка подмен невозможна по построению. Ссылка, которой нет в карте, остаётся
    как есть — это либо запись, чей код не менялся, либо ссылка наружу архива.
    """
    if not text:
        return text, 0

    rewritten = 0

    def substitute(match: re.Match[str]) -> str:
        nonlocal rewritten
        prefix, code = match.group(1), match.group(2)
        replacement = mapping.get((prefix, code))
        if replacement is None or replacement == code:
            return match.group(0)
        rewritten += 1
        return f"{prefix}@{replacement}"

    for pattern in REFERENCE_PATTERNS:
        text = pattern.sub(substitute, text)
    return text, rewritten


__all__ = [
    "REFERENCE_PATTERNS",
    "WEB_SEARCH_CODE_LEN",
    "collect_references",
    "rewrite_references",
]
