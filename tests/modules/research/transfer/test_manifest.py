"""Манифест архива — первое, что читает импорт, и единственная защита от чужого файла.

Разбор обязан отказывать **своей** ошибкой: манифест приезжает извне, и `JSONDecodeError`,
выпавший наружу, стал бы 500-й там, где человеку нужно «возьмите другой файл».
"""

from __future__ import annotations

import json

import pytest

from src.modules.research.transfer.constants import ARCHIVE_FORMAT, ARCHIVE_FORMAT_VERSION
from src.modules.research.transfer.errors import ArchiveError
from src.modules.research.transfer.manifest import (
    Manifest,
    ManifestFile,
    ManifestRoot,
    ManifestSource,
    manifest_bytes,
    parse_manifest,
)

pytestmark = pytest.mark.pure


def _manifest(**overrides) -> dict:
    document = {
        "format": ARCHIVE_FORMAT,
        "format_version": ARCHIVE_FORMAT_VERSION,
        "archive_id": "01JB0000000000000000000000",
        "created_at": "2026-01-02 03:04:05",
        "source": {"install_id": "01JB1111111111111111111111", "app_version": "1.2.3"},
        "roots": [{"type": "research", "code": "0123456789", "title": "Исследование"}],
        "counts": {"research": 1},
        "files": [{"path": "rows/research.jsonl", "bytes": 10, "sha256": "ab" * 32}],
        "dangling_refs": [],
    }
    return {**document, **overrides}


def _raw(**overrides) -> bytes:
    return json.dumps(_manifest(**overrides), ensure_ascii=False).encode("utf-8")


def test_a_manifest_of_this_format_is_read_back_whole():
    manifest = parse_manifest(_raw())
    assert manifest.format == ARCHIVE_FORMAT
    assert manifest.archive_id == "01JB0000000000000000000000"
    assert [root.code for root in manifest.roots] == ["0123456789"]
    assert manifest.files[0].path == "rows/research.jsonl"


def test_a_written_manifest_survives_the_round_trip():
    """Пишущая и читающая стороны — одна пара: расхождение здесь означает архив, который не
    читается собственным приложением."""
    original = Manifest(
        format=ARCHIVE_FORMAT,
        format_version=ARCHIVE_FORMAT_VERSION,
        archive_id="01JB0000000000000000000000",
        created_at="2026-01-02 03:04:05",
        source=ManifestSource(install_id="one", app_version="1.2.3", alembic_heads=["abc"]),
        roots=[ManifestRoot(type="research", code="0123456789", title="Исследование «кавычки»")],
        counts={"research": 1, "areas": 2},
        files=[ManifestFile(path="rows/research.jsonl", bytes=10, sha256="ab" * 32)],
        dangling_refs=["AREA@0123456789"],
    )
    assert parse_manifest(manifest_bytes(original)) == original


def test_a_foreign_format_is_refused():
    with pytest.raises(ArchiveError, match="не является архивом исследования"):
        parse_manifest(_raw(format="some.other.tool"))


def test_a_newer_format_version_is_refused_and_says_so():
    """Отказ обязан назвать обе версии: иначе человек не поймёт, что чинится обновлением."""
    with pytest.raises(ArchiveError, match="обновите приложение") as refusal:
        parse_manifest(_raw(format_version=ARCHIVE_FORMAT_VERSION + 1))
    assert str(ARCHIVE_FORMAT_VERSION + 1) in str(refusal.value)
    assert str(ARCHIVE_FORMAT_VERSION) in str(refusal.value)


def test_an_older_format_version_is_accepted():
    """Версия отвечает на один вопрос — прочтёт ли ЭТА сборка ЭТОТ файл; старый файл прочтётся."""
    assert parse_manifest(_raw(format_version=ARCHIVE_FORMAT_VERSION - 1)).format_version == (
        ARCHIVE_FORMAT_VERSION - 1
    )


def test_a_manifest_without_an_archive_id_is_refused():
    """Идентификатор выгрузки — соль подмены кодов: без него карта перевыпуска невоспроизводима."""
    with pytest.raises(ArchiveError, match="идентификатора выгрузки"):
        parse_manifest(_raw(archive_id=""))


def test_a_manifest_without_roots_is_refused():
    with pytest.raises(ArchiveError, match="нет ни одного исследования"):
        parse_manifest(_raw(roots=[]))


@pytest.mark.parametrize(
    "field", ["format", "format_version", "archive_id", "created_at"],
    ids=["format", "version", "archive-id", "created-at"],
)
def test_a_manifest_missing_a_required_field_is_refused(field):
    document = _manifest()
    del document[field]
    with pytest.raises(ArchiveError, match="повреждён или не читается"):
        parse_manifest(json.dumps(document).encode("utf-8"))


def test_a_field_of_the_wrong_type_is_refused():
    with pytest.raises(ArchiveError, match="повреждён или не читается"):
        parse_manifest(_raw(format_version="первая"))


@pytest.mark.parametrize(
    "raw", [b"", b"{", b"not json at all", b"[]"], ids=["empty", "cut", "text", "array"]
)
def test_broken_json_is_refused_as_an_archive_error(raw):
    with pytest.raises(ArchiveError, match="повреждён или не читается"):
        parse_manifest(raw)


def test_bytes_that_are_not_utf8_are_refused_as_an_archive_error():
    with pytest.raises(ArchiveError, match="повреждён или не читается"):
        parse_manifest('{"format": "uroboros.research"}'.encode("utf-16"))
