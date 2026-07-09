"""Body-редактор — общие правки markdown-тела сущности по префиксу кода.

Тело есть у ``RESEARCH@`` / ``AREA@`` / ``NOTE@`` (у поиска — только ссылки, у источника —
контент страницы read-only). Тул отдаёт **код с префиксом** → по нему выбираем модель, снимаем
префикс, грузим строку, применяем чистый трансформ к ``body`` и сохраняем.

Трансформы — чистые функции над строкой; ошибка ввода (не найдено / неоднозначно) → ``ValueError``.
"""

from __future__ import annotations

from src.core.database import session_scope
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


# ── чистые трансформы над строкой тела ───────────────────────────────────────
def op_set(body: str, *, text: str) -> str:
    return text


def op_append(body: str, *, text: str, position: str) -> str:
    if position == "start":
        return text + body
    if position == "end":
        return body + text
    raise ValueError("position must be 'start' or 'end'.")


def op_insert(body: str, *, text: str, anchor: str, position: str) -> str:
    count = body.count(anchor)
    if count == 0:
        raise ValueError(f"Anchor {anchor!r} not found in body.")
    if count > 1:
        raise ValueError(f"Anchor {anchor!r} occurs {count} times — must be unique.")
    idx = body.index(anchor)
    if position == "before":
        return body[:idx] + text + body[idx:]
    if position == "after":
        cut = idx + len(anchor)
        return body[:cut] + text + body[cut:]
    raise ValueError("position must be 'before' or 'after'.")


def op_replace(body: str, *, find: str, text: str) -> str:
    count = body.count(find)
    if count == 0:
        raise ValueError(f"{find!r} not found in body.")
    if count > 1:
        raise ValueError(f"{find!r} occurs {count} times — must be unique to replace.")
    return body.replace(find, text, 1)


def _heading_level(line: str) -> int:
    """Уровень markdown-заголовка (число ведущих ``#``), или 0 если строка не заголовок."""
    stripped = line.lstrip()
    hashes = len(stripped) - len(stripped.lstrip("#"))
    if hashes == 0:
        return 0
    if len(stripped) == hashes or stripped[hashes] == " ":
        return hashes
    return 0


def op_replace_block(body: str, *, heading: str, text: str) -> str:
    """Заменить блок заголовка ``heading`` (весь текст до следующего заголовка того же/выше
    уровня) на ``text``. Ошибка, если заголовок не найден."""
    target = heading.strip()
    level = _heading_level(target)
    if level == 0:
        raise ValueError(f"{heading!r} is not a markdown heading (expected '# ...').")
    lines = body.split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.strip() == target), None)
    if start is None:
        raise ValueError(f"Heading {target!r} not found in body.")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        lvl = _heading_level(lines[j])
        if lvl and lvl <= level:
            end = j
            break
    return "\n".join(lines[:start] + text.split("\n") + lines[end:])


async def apply(code: str, mutate) -> Research | ResearchArea | ResearchNote:
    """Применить трансформ ``mutate(body) -> body`` к телу сущности ``code`` (с префиксом).

    Возвращает обновлённую ORM-строку (несёт ``code`` голый, ``body``, ``updated_at``).
    ``ValueError`` — неподдерживаемый префикс / сущность не найдена / ошибка трансформа.
    """
    model = _model_for(code)
    bare = strip_prefix(code)
    async with session_scope() as s:
        row = await s.get(model, bare)
        if row is None:
            raise ValueError(f"{code} not found.")
        row.body = mutate(row.body or "")
        await s.flush()
        await s.refresh(row)
    return row


__all__ = [
    "apply",
    "op_set",
    "op_append",
    "op_insert",
    "op_replace",
    "op_replace_block",
]
