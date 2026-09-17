"""Перевыпуск кода при столкновении с местной базой — детерминированно, а не случайно.

Случайный ``random_hash()`` для подмены не годится: при повторном заходе он выдаст другое
значение, и прерванный импорт, продолженный со второй попытки, создал бы второй комплект
записей вместо продолжения первого. Код **выводится** из идентификатора выгрузки и старого
кода, поэтому тот же архив в той же базе всегда строит ту же карту и ничего не хранит между
заходами.

Соль — ``archive_id`` из манифеста: две выгрузки одного исследования получают разные подмены и
обе копии могут лежать в базе рядом.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from src.core.utils.hashing import text_hash

CodesInUse = Callable[[list[str]], Awaitable[set[str]]]


def substitute_code(archive_id: str, origin_code: str, attempt: int) -> str:
    """Подменный код той же длины и того же алфавита, что исходный."""
    return text_hash(f"{archive_id}:{origin_code}:{attempt}")[: len(origin_code)]


async def assign_substitutes(
    *,
    archive_id: str,
    origins: list[str],
    codes_in_use: CodesInUse,
    reserved: set[str],
) -> dict[str, str]:
    """``старый код → свободный подменный`` для кодов, занятых чужими записями.

    Свобода проверяется дважды — против базы и против уже розданных подмен (``reserved``):
    без второй проверки два разных кода архива могли бы получить одно значение и схлопнуться
    в одну запись. Столкновение подмены разрешается следующей попыткой, а не случайным
    кодом, — детерминизм карты важнее краткости цикла.
    """
    assigned: dict[str, str] = {}
    pending = {origin: 0 for origin in origins}

    while pending:
        candidates = {
            origin: substitute_code(archive_id, origin, attempt)
            for origin, attempt in pending.items()
        }
        taken = await codes_in_use(list(candidates.values()))
        next_pending: dict[str, int] = {}
        for origin, candidate in candidates.items():
            if candidate in taken or candidate in reserved:
                next_pending[origin] = pending[origin] + 1
                continue
            assigned[origin] = candidate
            reserved.add(candidate)
        pending = next_pending

    return assigned


__all__ = ["CodesInUse", "assign_substitutes", "substitute_code"]
