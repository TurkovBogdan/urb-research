"""Body-редактор — общие правки markdown-тела сущности по префиксу кода.

Тело есть у ``RESEARCH@`` / ``AREA@`` / ``NOTE@`` (у поиска — только ссылки, у источника —
контент страницы read-only). Тул отдаёт **код с префиксом** → по нему выбираем модель, снимаем
префикс, грузим строку, применяем чистый трансформ к ``body`` и сохраняем.

Трансформы — чистые функции над строкой; ошибка ввода (не найдено / неоднозначно) → ``ValueError``.
Почти каждая возвращает пару ``(новое тело, отчёт)`` и едет через ``apply_edit``: наружу идёт не
тело целиком, а **шов** — окно тела по обе стороны от вставки, где сам вставленный текст заменён
заглушкой. Текст прислал агент; назад ему нужно ровно то, чего он не знает, — как вставка легла.

Заголовок ищется только вне ограждённого кода: строка ``# comment`` внутри ```` ``` ````-блока —
не заголовок, и раздел, в котором такой блок лежит, иначе обрывался бы на середине фенса.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import NamedTuple, TypeVar

from src.core.database import write_scope
from src.modules.research.codes import strip_prefix
from src.modules.research.constants import (
    AREA_CODE_PREFIX,
    NOTE_CODE_PREFIX,
    RESEARCH_CODE_PREFIX,
)
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research

_MODEL_BY_PREFIX = {
    RESEARCH_CODE_PREFIX: Research,
    AREA_CODE_PREFIX: ResearchArea,
    NOTE_CODE_PREFIX: ResearchNote,
}


def _model_for(code: str):
    prefix = code.split("@", 1)[0] if "@" in code else ""
    model = _MODEL_BY_PREFIX.get(prefix)
    if model is None:
        raise ValueError(
            f"Body editing is not supported for {code!r} — pass a RESEARCH@ / AREA@ / NOTE@ code."
        )
    return model


PREVIEW_WINDOW_CHARS = 128
SEAM_TEXT_PLACEHOLDER = "<text>"
SEAM_TRUNCATION_MARK = "…"
PREVIEW_ELISION_MARK = " … "


def _seam(before: str, after: str) -> str:
    """Шов правки: по ``PREVIEW_WINDOW_CHARS`` символов тела по обе стороны от вставленного
    текста, сам текст — заглушкой (его прислал агент, возвращать его назад незачем).

    ``…`` ставится только там, где окно обрезано серединой тела: край тела и так виден по тому,
    что окно кончилось, а неразличимые эти два случая заставляли бы гадать.
    """
    head = before[-PREVIEW_WINDOW_CHARS:]
    tail = after[:PREVIEW_WINDOW_CHARS]
    opening = SEAM_TRUNCATION_MARK if len(before) > PREVIEW_WINDOW_CHARS else ""
    closing = SEAM_TRUNCATION_MARK if len(after) > PREVIEW_WINDOW_CHARS else ""
    return f"{opening}{head}{SEAM_TEXT_PLACEHOLDER}{tail}{closing}"


def _elided(text: str) -> str:
    """Предпросмотр фрагмента: начало и конец по ``PREVIEW_WINDOW_CHARS`` символов через маркер
    пропуска; фрагмент короче двух окон отдаётся целиком — иначе половины дублировали бы друг
    друга."""
    if len(text) <= PREVIEW_WINDOW_CHARS * 2:
        return text
    return f"{text[:PREVIEW_WINDOW_CHARS]}{PREVIEW_ELISION_MARK}{text[-PREVIEW_WINDOW_CHARS:]}"


# ── чистые трансформы над строкой тела ───────────────────────────────────────
def op_set(body: str, *, text: str) -> str:
    return text


def op_append(body: str, *, text: str, position: str) -> tuple[str, str]:
    if position == "start":
        return text + body, _seam("", body)
    if position == "end":
        return body + text, _seam(body, "")
    raise ValueError("position must be 'start' or 'end'.")


def op_insert(body: str, *, text: str, anchor: str, position: str) -> tuple[str, str]:
    count = body.count(anchor)
    if count == 0:
        raise ValueError(f"Anchor {anchor!r} not found in body.")
    if count > 1:
        raise ValueError(f"Anchor {anchor!r} occurs {count} times — must be unique.")
    idx = body.index(anchor)
    if position == "before":
        return body[:idx] + text + body[idx:], _seam(body[:idx], body[idx:])
    if position == "after":
        cut = idx + len(anchor)
        return body[:cut] + text + body[cut:], _seam(body[:cut], body[cut:])
    raise ValueError("position must be 'before' or 'after'.")


def _replacement_seams(body: str, *, find: str) -> list[str]:
    """Швы всех вхождений ``find`` в порядке документа, каждый — окном по исходному телу.

    Вхождения ближе окна друг к другу отдают общий текст дважды: склеивать их значило бы
    отвечать на «сколько раз заменено» переменным числом швов.
    """
    seams = []
    at = body.find(find)
    while at != -1:
        seams.append(_seam(body[:at], body[at + len(find):]))
        at = body.find(find, at + len(find))
    return seams


def _searchable(find: str) -> str:
    """Пустая строка встречается везде и нигде не кончается: ``find`` её не сдвигает, и обход
    вхождений не завершается — до исчерпания памяти вместе с процессом сервера."""
    if not find:
        raise ValueError("find must not be empty — pass the text to look for.")
    return find


def op_replace(body: str, *, find: str, text: str) -> tuple[str, list[str]]:
    """Заменить единственное вхождение ``find``; вернуть тело и шов этой замены."""
    count = body.count(_searchable(find))
    if count == 0:
        raise ValueError(f"{find!r} not found in body.")
    if count > 1:
        raise ValueError(f"{find!r} occurs {count} times — must be unique to replace.")
    return body.replace(find, text, 1), _replacement_seams(body, find=find)


def op_replace_all(body: str, *, find: str, text: str) -> tuple[str, list[str]]:
    """Заменить все вхождения ``find``; вернуть тело и швы всех замен по порядку."""
    seams = _replacement_seams(body, find=_searchable(find))
    if not seams:
        raise ValueError(f"{find!r} not found in body.")
    return body.replace(find, text), seams


HEADING_PATH_SEPARATOR = " > "

_FENCE_LINE = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})(?P<info>.*)$")


def _heading_level(line: str) -> int:
    """Уровень markdown-заголовка (число ведущих ``#``), или 0 если строка не заголовок."""
    stripped = line.lstrip()
    hashes = len(stripped) - len(stripped.lstrip("#"))
    if hashes == 0:
        return 0
    if len(stripped) == hashes or stripped[hashes] == " ":
        return hashes
    return 0


def _closes_fence(fence: "re.Match[str]", opened: str) -> bool:
    """Фенс закрывает открытый: тот же символ, не короче и без языка после него."""
    return (
        fence["marker"][0] == opened[0]
        and len(fence["marker"]) >= len(opened)
        and not fence["info"].strip()
    )


def _heading_levels(lines: Sequence[str]) -> list[int]:
    """Уровень заголовка для каждой строки тела; 0 — не заголовок, в том числе внутри фенса."""
    levels = []
    opened = ""
    for line in lines:
        fence = _FENCE_LINE.match(line)
        if opened:
            if fence and _closes_fence(fence, opened):
                opened = ""
            levels.append(0)
        elif fence:
            opened = fence["marker"]
            levels.append(0)
        else:
            levels.append(_heading_level(line))
    return levels


class _Scope(NamedTuple):
    """Полуинтервал строк, внутри которого ищется очередной сегмент пути."""

    start: int
    limit: int


def _block_end(levels: Sequence[int], start: int, limit: int) -> int:
    """Строка, на которой обрывается блок заголовка ``start``: следующий заголовок того же или
    более высокого уровня, иначе ``limit``."""
    level = levels[start]
    for index in range(start + 1, limit):
        if levels[index] and levels[index] <= level:
            return index
    return limit


def _block_scope(levels: Sequence[int], heading_index: int, outer: _Scope) -> _Scope:
    return _Scope(heading_index + 1, _block_end(levels, heading_index, outer.limit))


def _heading_matches(
    lines: Sequence[str], levels: Sequence[int], segment: str, scope: _Scope
) -> list[int]:
    """Строки внутри ``scope``, совпадающие с сегментом целиком (после ``strip``) — и уровнем."""
    return [
        index
        for index in range(scope.start, scope.limit)
        if levels[index] and lines[index].strip() == segment
    ]


def _enclosing_heading(
    lines: Sequence[str], levels: Sequence[int], index: int, scope: _Scope
) -> str | None:
    """Ближайший заголовок выше уровнем, внутри блока которого лежит строка ``index``."""
    for above in range(index - 1, scope.start - 1, -1):
        if levels[above] and levels[above] < levels[index]:
            return lines[above].strip()
    return None


def _path_example(
    lines: Sequence[str],
    levels: Sequence[int],
    segment: str,
    matches: Sequence[int],
    scope: _Scope,
    resolved: Sequence[str],
) -> str | None:
    """Путь из заголовков самого тела, который развёл бы найденные дубликаты; ``None`` — ни один
    объемлющий заголовок их не различает, и путь тут не поможет вовсе."""
    for index in matches:
        parent = _enclosing_heading(lines, levels, index, scope)
        if parent is None:
            continue
        parent_matches = _heading_matches(lines, levels, parent, scope)
        if len(parent_matches) != 1:
            continue
        inside_parent = _block_scope(levels, parent_matches[0], scope)
        if len(_heading_matches(lines, levels, segment, inside_parent)) == 1:
            return HEADING_PATH_SEPARATOR.join([*resolved, parent, segment])
    return None


def _segment_index(
    lines: Sequence[str],
    levels: Sequence[int],
    segment: str,
    scope: _Scope,
    resolved: Sequence[str],
) -> int:
    """Единственная строка сегмента внутри ``scope``; ноль совпадений и два — отказ.

    Неоднозначность именно отказ, а не первое совпадение: молча взятый первый раздел переписывал
    бы не тот, о котором агент думал, и узнать об этом было бы неоткуда.
    """
    if _heading_level(segment) == 0:
        raise ValueError(
            f"{segment!r} is not a markdown heading — every segment must carry its own '#', "
            f"e.g. '## Section{HEADING_PATH_SEPARATOR}### Subsection'."
        )
    matches = _heading_matches(lines, levels, segment, scope)
    where = f"inside {resolved[-1]!r}" if resolved else "in the body"
    if not matches:
        raise ValueError(f"Heading {segment!r} not found {where}.")
    if len(matches) > 1:
        example = _path_example(lines, levels, segment, matches, scope, resolved)
        if example is None:
            raise ValueError(
                f"Heading {segment!r} occurs {len(matches)} times {where} — it must name exactly "
                f"one section, and no enclosing heading tells these apart, so a path "
                f"({HEADING_PATH_SEPARATOR.join(('## Section', '### Subsection'))!r}) cannot "
                f"single one out either. Rename one of them, or replace the section holding them."
            )
        raise ValueError(
            f"Heading {segment!r} occurs {len(matches)} times {where} — it must name exactly one "
            f"section. Say which one with a path, segments separated by "
            f"{HEADING_PATH_SEPARATOR!r}: {example!r}."
        )
    return matches[0]


def _heading_index(lines: Sequence[str], levels: Sequence[int], heading: str) -> int:
    """Строка заголовка, названного ``heading`` — голым заголовком или путём ``A > B``.

    Первый сегмент обязан быть единственным в теле, каждый следующий — единственным внутри
    блока предыдущего, на любой глубине.
    """
    segments = [segment.strip() for segment in heading.split(HEADING_PATH_SEPARATOR)]
    scope = _Scope(0, len(lines))
    index = _segment_index(lines, levels, segments[0], scope, resolved=[])
    for depth, segment in enumerate(segments[1:], start=1):
        scope = _block_scope(levels, index, scope)
        index = _segment_index(lines, levels, segment, scope, resolved=segments[:depth])
    return index


class SectionCut(NamedTuple):
    """Что вырезала правка раздела: предпросмотр блока, его полная длина и заголовок, оборвавший
    его (``None`` — тело кончилось).

    Границу раздела считает сервер по уровню заголовка, так что непредсказуем для агента именно
    размах выреза: хвост блока и его длина отвечают на это прямо, а шов вокруг нового текста
    выглядел бы одинаково аккуратно и при вырезе вдвое шире нужного.
    """

    removed: str
    removed_length: int
    stopped_at: str | None


def op_set_section(body: str, *, heading: str, text: str) -> tuple[str, SectionCut]:
    """Заменить раздел ``heading`` (от его строки до следующего заголовка того же или более
    высокого уровня, вместе с подразделами) на ``text``; вернуть тело и вырезанный блок."""
    lines = body.split("\n")
    levels = _heading_levels(lines)
    start = _heading_index(lines, levels, heading)
    end = _block_end(levels, start, len(lines))
    removed = "\n".join(lines[start:end])
    cut = SectionCut(
        removed=_elided(removed),
        removed_length=len(removed),
        stopped_at=lines[end].strip() if end < len(lines) else None,
    )
    return "\n".join(lines[:start] + text.split("\n") + lines[end:]), cut


Entity = Research | ResearchArea | ResearchNote
Report = TypeVar("Report")


async def apply_edit(code: str, edit: Callable[[str], tuple[str, Report]]) -> tuple[Entity, Report]:
    """Применить правку ``edit(body) -> (новое тело, отчёт)`` к телу сущности ``code`` (с префиксом).

    Возвращает обновлённую ORM-строку (несёт ``code`` голый, ``body``, ``updated_at``) и отчёт
    правки. ``ValueError`` — неподдерживаемый префикс / сущность не найдена / ошибка трансформа.
    """
    model = _model_for(code)
    bare = strip_prefix(code)
    async with write_scope() as s:
        row = await s.get(model, bare)
        if row is None:
            raise ValueError(f"{code} not found.")
        row.body, report = edit(row.body or "")
        await s.flush()
        await s.refresh(row)
    return row, report


async def apply(code: str, mutate: Callable[[str], str]) -> Entity:
    """``apply_edit`` для правки, которой нечего сообщить о себе сверх нового тела."""
    row, _ = await apply_edit(code, lambda body: (mutate(body), None))
    return row


__all__ = [
    "HEADING_PATH_SEPARATOR",
    "PREVIEW_ELISION_MARK",
    "PREVIEW_WINDOW_CHARS",
    "SEAM_TEXT_PLACEHOLDER",
    "SEAM_TRUNCATION_MARK",
    "SectionCut",
    "apply",
    "apply_edit",
    "op_set",
    "op_append",
    "op_insert",
    "op_replace",
    "op_replace_all",
    "op_set_section",
]
