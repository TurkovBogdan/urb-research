"""Манифест архива — контракт между двумя установками.

Импорт читает его первым и по нему принимает три решения до любой работы с базой: берём ли мы
этот формат, дошёл ли файл целым и что окажется в базе, если нажать «Импортировать».
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from src.modules.research.transfer.constants import ARCHIVE_FORMAT, ARCHIVE_FORMAT_VERSION
from src.modules.research.transfer.errors import ArchiveError


class ManifestSource(BaseModel):
    """Откуда снят архив. Только для разбора инцидентов и для подсказки «это моя же установка»."""

    install_id: str = ""
    app_version: str = ""
    alembic_heads: list[str] = Field(default_factory=list)


class ManifestRoot(BaseModel):
    """Корень архива — исследование, ради которого он снят."""

    type: str
    code: str
    title: str


class ManifestFile(BaseModel):
    """Запись инвентаря: путь, размер несжатого содержимого и его sha256."""

    path: str
    bytes: int
    sha256: str


class Manifest(BaseModel):
    format: str
    format_version: int
    archive_id: str
    created_at: str
    source: ManifestSource = Field(default_factory=ManifestSource)
    roots: list[ManifestRoot] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    files: list[ManifestFile] = Field(default_factory=list)
    dangling_refs: list[str] = Field(default_factory=list)


def manifest_bytes(manifest: Manifest) -> bytes:
    return manifest.model_dump_json(indent=2).encode("utf-8")


def parse_manifest(raw: bytes) -> Manifest:
    """Разобрать манифест и отказать всему, что этой сборке не по зубам."""
    try:
        manifest = Manifest.model_validate(json.loads(raw.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
        raise ArchiveError("манифест архива повреждён или не читается") from error

    if manifest.format != ARCHIVE_FORMAT:
        raise ArchiveError("файл не является архивом исследования")
    if manifest.format_version > ARCHIVE_FORMAT_VERSION:
        raise ArchiveError(
            f"архив сделан более новой версией формата ({manifest.format_version} против "
            f"{ARCHIVE_FORMAT_VERSION}) — обновите приложение"
        )
    if not manifest.archive_id:
        raise ArchiveError("в манифесте нет идентификатора выгрузки")
    if not manifest.roots:
        raise ArchiveError("в архиве нет ни одного исследования")
    return manifest


__all__ = [
    "Manifest",
    "ManifestFile",
    "ManifestRoot",
    "ManifestSource",
    "manifest_bytes",
    "parse_manifest",
]
