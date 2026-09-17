"""Загруженный архив во временной папке: приём, поиск по идентификатору, уборка.

Файл живёт между тремя запросами (загрузка → разбор → применение), поэтому ему нужно место на
диске и имя, которое нельзя подделать. Имя — идентификатор загрузки, а не то, что прислал
браузер: пользовательская строка в путь не попадает вовсе.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from fastapi import UploadFile
from ulid import ULID

from src.core.app_path import AppPath
from src.core.utils.date import utc_now
from src.modules.research.transfer.constants import ARCHIVE_EXTENSION, MAX_UPLOAD_BYTES
from src.modules.research.transfer.errors import ArchiveError

_UPLOAD_ID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
_CHUNK = 1024 * 1024

# Фонового рабочего в установке может не быть вовсе, поэтому уборка висит на самой загрузке:
# следующий импорт выметает то, что осталось от брошенных заходов.
UPLOAD_LIFETIME = timedelta(days=1)


@dataclass(frozen=True)
class StoredUpload:
    """Принятый файл: чем его звать дальше и что показать человеку."""

    upload_id: str
    file_name: str
    size: int
    path: Path


def uploads_directory() -> Path:
    directory = AppPath.from_root().tmp / "import"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def upload_path(upload_id: str) -> Path:
    """Путь загрузки по идентификатору; чужая форма идентификатора — отказ, а не поиск файла."""
    if not _UPLOAD_ID.match(upload_id):
        raise ArchiveError("неизвестная загрузка")
    path = uploads_directory() / f"{upload_id}{ARCHIVE_EXTENSION}"
    if not path.exists():
        raise ArchiveError("загрузка не найдена или уже удалена")
    return path


async def store_upload(file: UploadFile) -> StoredUpload:
    """Положить присланный файл во временную папку, считая объём по факту чтения."""
    sweep_stale_uploads()
    upload_id = str(ULID())
    path = uploads_directory() / f"{upload_id}{ARCHIVE_EXTENSION}"
    written = 0
    with path.open("wb") as target:
        while chunk := await file.read(_CHUNK):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                target.close()
                path.unlink(missing_ok=True)
                raise ArchiveError("файл больше допустимого предела")
            target.write(chunk)
    stored = StoredUpload(
        upload_id=upload_id, file_name=file.filename or path.name, size=written, path=path
    )
    _passport_path(upload_id).write_text(
        json.dumps({"file_name": stored.file_name, "size": written}, ensure_ascii=False),
        encoding="utf-8",
    )
    return stored


def upload_info(upload_id: str) -> StoredUpload:
    """Паспорт загрузки: имя, каким файл пришёл, и его размер.

    Имя браузера не годится в качестве имени файла на диске, но показать его человеку на
    странице разбора нужно — поэтому оно лежит рядом отдельной запиской.
    """
    path = upload_path(upload_id)
    passport = _passport_path(upload_id)
    known = json.loads(passport.read_text(encoding="utf-8")) if passport.exists() else {}
    return StoredUpload(
        upload_id=upload_id,
        file_name=known.get("file_name", path.name),
        size=known.get("size", path.stat().st_size),
        path=path,
    )


def drop_upload(upload_id: str) -> None:
    (uploads_directory() / f"{upload_id}{ARCHIVE_EXTENSION}").unlink(missing_ok=True)
    _passport_path(upload_id).unlink(missing_ok=True)


def sweep_stale_uploads() -> None:
    """Выбросить загрузки, брошенные больше суток назад."""
    deadline = (utc_now() - UPLOAD_LIFETIME).timestamp()
    for path in uploads_directory().iterdir():
        if path.is_file() and path.stat().st_mtime < deadline:
            path.unlink(missing_ok=True)


def _passport_path(upload_id: str) -> Path:
    return uploads_directory() / f"{upload_id}.json"


def export_directory() -> Path:
    """Куда складывать собранные архивы до отдачи: тот же рантайм, отдельная папка."""
    directory = AppPath.from_root().tmp / "export"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def drop_export(path: Path) -> None:
    """Снять отданный архив с диска — вызывается фоновой задачей ответа."""
    path.unlink(missing_ok=True)


__all__ = [
    "StoredUpload",
    "UPLOAD_LIFETIME",
    "drop_export",
    "drop_upload",
    "export_directory",
    "store_upload",
    "sweep_stale_uploads",
    "upload_info",
    "upload_path",
    "uploads_directory",
]
