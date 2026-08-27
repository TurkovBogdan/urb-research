"""CRUD ``ResearchGroup`` — группы исследований. Каждая функция владеет сессией.

Группа — раскладка реестра, а не часть пайплайна: удаление группы не трогает сами исследования, оно
их **отвязывает** (``group_code`` → ``NULL``). Декларация ``ON DELETE SET NULL`` на SQLite не
исполняется (FK-каскад выключен), поэтому отвязку делает ``group_delete`` — тем же ручным способом,
что и остальные каскады модуля.

Размеры title/description/icon/color — мягкое усечение (``_clip`` по code points, кириллица-safe),
как в ``crud/area.py``, а не ошибка валидации.
"""

from __future__ import annotations

from sqlalchemy import func, select, update

from src.core.database import session_scope
from src.core.utils.hashing import random_hash
from src.modules.research.constants import (
    GROUP_COLOR_MAX,
    GROUP_DESCRIPTION_MAX,
    GROUP_ICON_MAX,
    GROUP_RESEARCHES_DELETE,
    GROUP_RESEARCHES_DETACH,
    GROUP_RESEARCHES_MOVE,
    GROUP_TITLE_MAX,
)
from src.modules.research.crud import research as research_crud
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.research import Research


def group_code() -> str:
    """Код группы — голый 22-hex ``random_hash`` (естественного ключа дедупа нет).

    Тип-префикс (``GROUP@``) — презентация, надевается на границе (см. ``research.codes``).
    """
    return random_hash()


def _clip(value: str | None, limit: int) -> str:
    """Усечь строку до ``limit`` символов Unicode; ``None`` → ``""`` (поле не nullable)."""
    return (value or "")[:limit]


async def group_create(
    *,
    title: str,
    description: str | None = None,
    icon: str | None = None,
    color: str | None = None,
    sort: int | None = None,
) -> ResearchGroup:
    """Создать группу. ``sort`` не задан → ``GROUP_SORT_DEFAULT`` (дефолт модели)."""
    async with session_scope() as s:
        row = ResearchGroup(
            code=group_code(),
            title=_clip(title, GROUP_TITLE_MAX),
            description=_clip(description, GROUP_DESCRIPTION_MAX),
            icon=_clip(icon, GROUP_ICON_MAX),
            color=_clip(color, GROUP_COLOR_MAX),
        )
        if sort is not None:
            row.sort = sort
        s.add(row)
        await s.flush()
        await s.refresh(row)
    return row


async def group_get(code: str) -> ResearchGroup | None:
    async with session_scope() as s:
        return await s.get(ResearchGroup, code)


def _researches_of_group(column):
    """Скалярный подзапрос «свести колонку по исследованиям этой группы».

    Коррелирует по ``group_code`` с внешней ``ResearchGroup``, поэтому годится прямо в ``ORDER BY``:
    счётчик и дата работы на карточке считаются отдельными GROUP BY (по кодам страницы), но
    сортировать по ним можно только в SQL.
    """
    return (
        select(column)
        .select_from(Research)
        .where(Research.group_code == ResearchGroup.code)
        .scalar_subquery()
    )


# По чему разрешено сортировать список полок (белый список = защита от инъекции: неизвестный
# ключ падает в дефолт). ``sort_by`` — ключ сортировки списка, ``sort`` — колонка позиции,
# которую человек выставляет руками; это разные вещи, отсюда и разные имена.
GROUP_SORT_BY_COLUMNS = {
    "research_updated_at": _researches_of_group(func.max(Research.updated_at)),
    "sort": ResearchGroup.sort,
    "title": ResearchGroup.title,
    "research_count": _researches_of_group(func.count()),
    "created_at": ResearchGroup.created_at,
}
# По умолчанию сверху та группа, где недавно работали: реестр читают, чтобы продолжить, а не
# чтобы посмотреть на расстановку.
GROUP_SORT_BY_DEFAULT = "research_updated_at"


async def group_list(
    *,
    sort_by: str = GROUP_SORT_BY_DEFAULT,
    sort_dir: str = "desc",
) -> list[ResearchGroup]:
    """Все группы в порядке показа. Неизвестный ключ падает в дефолт.

    Название и код — тайбрейк: у всех новых групп ``sort`` одинаковый (и дата работы у пустых
    групп отсутствует), без него порядок одинаковых строк менялся бы от запроса к запросу.

    Пустая группа уходит в конец при **любом** направлении: у неё нет ни даты работы, ни
    исследований, и это не «самая ранняя», а «ответа нет».
    """
    column = GROUP_SORT_BY_COLUMNS.get(sort_by, GROUP_SORT_BY_COLUMNS[GROUP_SORT_BY_DEFAULT])
    ordering = column.asc() if sort_dir == "asc" else column.desc()
    stmt = select(ResearchGroup).order_by(
        ordering.nulls_last(),
        ResearchGroup.title.asc(),
        ResearchGroup.code.asc(),
    )
    async with session_scope() as s:
        return list((await s.execute(stmt)).scalars().all())


async def group_search_texts() -> list[tuple[str, str]]:
    """``(code, весь текст группы одной строкой)`` по всем группам — сырьё для поиска по реестру."""
    stmt = select(ResearchGroup.code, ResearchGroup.title, ResearchGroup.description)
    async with session_scope() as s:
        rows = (await s.execute(stmt)).all()
    return [(code, "\n".join(filter(None, texts))) for code, *texts in rows]


async def group_update(
    code: str,
    *,
    title: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    color: str | None = None,
    sort: int | None = None,
) -> ResearchGroup | None:
    """Обновить переданные поля группы (``None`` = не трогать)."""
    async with session_scope() as s:
        row = await s.get(ResearchGroup, code)
        if row is None:
            return None
        if title is not None:
            row.title = _clip(title, GROUP_TITLE_MAX)
        if description is not None:
            row.description = _clip(description, GROUP_DESCRIPTION_MAX)
        if icon is not None:
            row.icon = _clip(icon, GROUP_ICON_MAX)
        if color is not None:
            row.color = _clip(color, GROUP_COLOR_MAX)
        if sort is not None:
            row.sort = sort
        await s.flush()
        await s.refresh(row)
    return row


async def group_delete(
    code: str,
    *,
    researches: str = GROUP_RESEARCHES_DETACH,
    move_to: str | None = None,
) -> bool:
    """Удалить группу, решив судьбу её исследований. ``True`` — существовала и удалена.

    ``researches``: ``detach`` — убрать из группы (``group_code`` → ``NULL``), ``move`` — перевесить
    в группу ``move_to``, ``delete`` — удалить сами исследования вместе с их содержимым.
    Существование ``move_to`` проверяет вызывающий: CRUD не решает, что считать ошибкой ввода.

    Удаление идёт через ``research_delete`` по одному, а не пачкой: каскад исследования (источники
    → поиски → заметки → области) описан там один раз, и дублировать его здесь значило бы завести
    второе место, где о нём надо помнить.
    """
    if researches == GROUP_RESEARCHES_DELETE:
        for research_code in await _research_codes_of(code):
            await research_crud.research_delete(research_code)

    async with session_scope() as s:
        row = await s.get(ResearchGroup, code)
        if row is None:
            return False
        if researches != GROUP_RESEARCHES_DELETE:
            moved = move_to if researches == GROUP_RESEARCHES_MOVE else None
            await s.execute(
                update(Research).where(Research.group_code == code).values(group_code=moved)
            )
        await s.delete(row)
    return True


async def _research_codes_of(group_code: str) -> list[str]:
    async with session_scope() as s:
        rows = await s.execute(
            select(Research.code).where(Research.group_code == group_code)
        )
        return [code for (code,) in rows.all()]


__all__ = [
    "GROUP_SORT_BY_COLUMNS",
    "GROUP_SORT_BY_DEFAULT",
    "group_code",
    "group_create",
    "group_get",
    "group_list",
    "group_search_texts",
    "group_update",
    "group_delete",
]
