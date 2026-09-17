"""Контейнер ``.urch``: запись и чтение zip с опознавательной записью и пределами разбора.

Своим форматом архив делает раскладка и манифест, а не способ упаковать байты, — поэтому
контейнер обычный zip из стандартной библиотеки. Отличает его от переименованного zip первая
запись ``mimetype``, положенная **без сжатия**: сигнатура оказывается в фиксированном смещении
от начала файла, и тип узнаётся по содержимому, а не по расширению.

Читатель считает архив недоверенным: имена записей сверяются с раскладкой, объём считается при
чтении (заголовку zip верить нельзя — он часть того же файла), суммы сверяются с манифестом.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from src.core.utils.date import datetime_to_agent, utc_now
from src.modules.research.transfer.constants import (
    ARCHIVE_FORMAT,
    ARCHIVE_FORMAT_VERSION,
    ARCHIVE_MEDIA_TYPE,
    BODY_DIRECTORY,
    MANIFEST_ENTRY,
    MAX_ENTRY_BYTES,
    MAX_TOTAL_UNCOMPRESSED_BYTES,
    MIMETYPE_ENTRY,
    PAGE_MATERIAL_DIRECTORY,
    ROW_ENTITIES,
    body_entry,
    page_material_entry,
    rows_entry,
)
from src.modules.research.transfer.errors import ArchiveError
from src.modules.research.transfer.manifest import (
    Manifest,
    ManifestFile,
    ManifestRoot,
    ManifestSource,
    manifest_bytes,
    parse_manifest,
)
from src.modules.research.transfer.refs import WEB_SEARCH_CODE_LEN
from src.modules.research.constants import CODE_LEN

_READ_CHUNK = 256 * 1024

# Имя записи участвует в сопоставлении «тело ↔ строка», поэтому разрешены ровно те формы,
# которые пишет экспорт: проверка строже, чем «нет ``..``», и заодно ловит мусор.
_ALLOWED_ENTRIES = (
    re.compile(rf"^{MIMETYPE_ENTRY}$"),
    re.compile(rf"^{MANIFEST_ENTRY}$"),
    re.compile(rf"^rows/({'|'.join(ROW_ENTITIES)})\.jsonl$"),
    re.compile(rf"^({'|'.join(BODY_DIRECTORY.values())})/[0-9a-f]{{{CODE_LEN}}}\.md$"),
    re.compile(rf"^{PAGE_MATERIAL_DIRECTORY}/[0-9a-f]{{{WEB_SEARCH_CODE_LEN}}}\.md$"),
)


class ArchiveWriter:
    """Пишущая сторона: записи уходят в файл по одной, суммы считаются на лету.

    Манифест пишется последним — он перечисляет суммы всех записей, а узнать их раньше, чем
    записи легли, нельзя. Порядок записей внутри zip на чтение не влияет (читатель берёт их по
    имени через центральный каталог); значима только первая запись — опознавательная.
    """

    def __init__(self, path: Path) -> None:
        self._zip = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
        self._files: list[ManifestFile] = []
        self._zip.writestr(
            zipfile.ZipInfo(MIMETYPE_ENTRY), ARCHIVE_MEDIA_TYPE, compress_type=zipfile.ZIP_STORED
        )

    def __enter__(self) -> "ArchiveWriter":
        return self

    def __exit__(self, *_exc: object) -> None:
        self._zip.close()

    def add_rows(self, entity: str, rows: list[dict[str, Any]]) -> None:
        payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        self._add(rows_entry(entity), payload)

    def add_body(self, entity: str, code: str, text: str) -> None:
        self._add(body_entry(entity, code), text)

    def add_page_material(self, code: str, text: str) -> None:
        self._add(page_material_entry(code), text)

    def finish(
        self,
        *,
        archive_id: str,
        source: ManifestSource,
        roots: list[ManifestRoot],
        counts: dict[str, int],
        dangling_refs: list[str],
    ) -> Manifest:
        manifest = Manifest(
            format=ARCHIVE_FORMAT,
            format_version=ARCHIVE_FORMAT_VERSION,
            archive_id=archive_id,
            created_at=datetime_to_agent(utc_now()),
            source=source,
            roots=roots,
            counts=counts,
            files=self._files,
            dangling_refs=dangling_refs,
        )
        self._zip.writestr(MANIFEST_ENTRY, manifest_bytes(manifest))
        return manifest

    def _add(self, entry: str, text: str) -> None:
        payload = text.encode("utf-8")
        self._zip.writestr(entry, payload)
        self._files.append(
            ManifestFile(
                path=entry, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()
            )
        )


class ArchiveReader:
    """Читающая сторона: проверки лестницей, от дешёвых к дорогим, и чтение по имени записи."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._zip: zipfile.ZipFile | None = None
        self.manifest: Manifest | None = None

    def __enter__(self) -> "ArchiveReader":
        if not zipfile.is_zipfile(self.path):
            raise ArchiveError("файл не является архивом .urch")
        self._zip = zipfile.ZipFile(self.path)
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._zip is not None:
            self._zip.close()

    def open_manifest(self) -> Manifest:
        """Опознать контейнер и разобрать манифест — всё, что делается до чтения содержимого."""
        names = self._archive.namelist()
        if not names or names[0] != MIMETYPE_ENTRY:
            raise ArchiveError("файл не является архивом .urch")
        if self._read_entry(MIMETYPE_ENTRY).decode("utf-8").strip() != ARCHIVE_MEDIA_TYPE:
            raise ArchiveError("файл не является архивом .urch")
        for name in names:
            if not any(pattern.match(name) for pattern in _ALLOWED_ENTRIES):
                raise ArchiveError(f"архив содержит недопустимую запись «{name}»")
        if MANIFEST_ENTRY not in names:
            raise ArchiveError("в архиве нет манифеста")

        self.manifest = parse_manifest(self._read_entry(MANIFEST_ENTRY))
        return self.manifest

    def verify_inventory(self) -> None:
        """Сверить состав и суммы: обещанное манифестом должно лежать в архиве байт в байт."""
        manifest = self._require_manifest()
        present = {name for name in self._archive.namelist()} - {MIMETYPE_ENTRY, MANIFEST_ENTRY}
        promised = {item.path for item in manifest.files}
        if promised != present:
            missing = ", ".join(sorted(promised - present)) or "—"
            extra = ", ".join(sorted(present - promised)) or "—"
            raise ArchiveError(
                f"состав архива не совпадает с манифестом (нет: {missing}; лишнее: {extra})"
            )
        for item in manifest.files:
            payload = self._read_entry(item.path)
            if len(payload) != item.bytes or hashlib.sha256(payload).hexdigest() != item.sha256:
                raise ArchiveError(f"запись «{item.path}» повреждена при передаче")

    def rows(self, entity: str) -> list[dict[str, Any]]:
        entry = rows_entry(entity)
        if entry not in self._archive.namelist():
            return []
        payload = self._read_entry(entry).decode("utf-8")
        # Строки режутся строго по ``\n``: ``splitlines`` рвёт ещё и по Unicode-разделителям
        # (U+2028, U+0085 и родня), а они живьём встречаются в материале страниц и остаются в
        # JSON как есть — запись разваливалась бы посреди строки.
        return [json.loads(line) for line in payload.split("\n") if line.strip()]

    def body(self, entity: str, code: str) -> str:
        return self._optional_text(body_entry(entity, code))

    def page_material(self, code: str) -> str | None:
        entry = page_material_entry(code)
        if entry not in self._archive.namelist():
            return None
        return self._read_entry(entry).decode("utf-8")

    def _optional_text(self, entry: str) -> str:
        if entry not in self._archive.namelist():
            return ""
        return self._read_entry(entry).decode("utf-8")

    @property
    def _archive(self) -> zipfile.ZipFile:
        if self._zip is None:
            raise ArchiveError("архив не открыт")
        return self._zip

    def _require_manifest(self) -> Manifest:
        if self.manifest is None:
            return self.open_manifest()
        return self.manifest

    def _read_entry(self, entry: str) -> bytes:
        """Прочитать запись целиком, считая объём по факту чтения, а не по заголовку zip."""
        chunks: list[bytes] = []
        read = 0
        with self._archive.open(entry) as stream:
            for chunk in iter(lambda: stream.read(_READ_CHUNK), b""):
                read += len(chunk)
                if read > MAX_ENTRY_BYTES:
                    raise ArchiveError(f"запись «{entry}» превышает предел распаковки")
                chunks.append(chunk)
        return b"".join(chunks)


def uncompressed_size(path: Path) -> int:
    """Суммарный несжатый объём по заголовкам — дешёвая прикидка до чтения содержимого."""
    if not zipfile.is_zipfile(path):
        raise ArchiveError("файл не является архивом .urch")
    with zipfile.ZipFile(path) as archive:
        return sum(item.file_size for item in archive.infolist())


def check_total_size(path: Path) -> None:
    if uncompressed_size(path) > MAX_TOTAL_UNCOMPRESSED_BYTES:
        raise ArchiveError("архив не проходит по пределам распаковки")


__all__ = [
    "ArchiveReader",
    "ArchiveWriter",
    "check_total_size",
    "uncompressed_size",
]
