"""Контейнер ``.urch``: что пишется, что читается обратно и чем читатель встречает чужой файл.

Архив приходит извне, поэтому у читателя две обязанности: вернуть ровно то, что было записано,
и отказать всему остальному **своей** ошибкой, назвав причину. Файловая система тут не «внешний
ресурс», а сам предмет проверки: zip без файла не существует, сети и базы в тесте нет.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from src.modules.research.transfer import archive as archive_module
from src.modules.research.transfer.archive import (
    ArchiveReader,
    ArchiveWriter,
    check_total_size,
    uncompressed_size,
)
from src.modules.research.transfer.constants import (
    ARCHIVE_MEDIA_TYPE,
    ENTITY_AREAS,
    ENTITY_NOTES,
    ENTITY_RESEARCH,
    MANIFEST_ENTRY,
    MIMETYPE_ENTRY,
    body_entry,
    page_material_entry,
    rows_entry,
)
from src.modules.research.transfer.errors import ArchiveError
from src.modules.research.transfer.manifest import ManifestRoot, ManifestSource

pytestmark = pytest.mark.pure

RESEARCH_CODE = "0123456789"
NOTE_CODE = "abcdef0123"
PAGE_CODE = "ab" * 11

RESEARCH_ROW = {"code": RESEARCH_CODE, "title": "Исследование «кавычки»", "created_at": None}
NOTE_ROW = {"code": NOTE_CODE, "title": "Заметка"}
BODY = "# Тело\n\nСсылка на AREA@abcdef0123 и перевод строки в конце\n"
MATERIAL = "Материал страницы — строка с эмодзи 🙂\n"


def _write_archive(path: Path) -> Path:
    with ArchiveWriter(path) as archive:
        archive.add_rows(ENTITY_RESEARCH, [RESEARCH_ROW])
        archive.add_rows(ENTITY_NOTES, [NOTE_ROW])
        archive.add_body(ENTITY_RESEARCH, RESEARCH_CODE, BODY)
        archive.add_page_material(PAGE_CODE, MATERIAL)
        archive.finish(
            archive_id="01JB0000000000000000000000",
            source=ManifestSource(install_id="01JB1111111111111111111111", app_version="1.2.3"),
            roots=[ManifestRoot(type=ENTITY_RESEARCH, code=RESEARCH_CODE, title="Исследование")],
            counts={ENTITY_RESEARCH: 1, ENTITY_NOTES: 1},
            dangling_refs=[],
        )
    return path


def _entries(path: Path) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(path) as source:
        return [(name, source.read(name)) for name in source.namelist()]


def _pack(path: Path, entries: list[tuple[str, bytes]]) -> Path:
    """Собрать zip из готовых записей, сохранив порядок и несжатость первой."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for position, (name, payload) in enumerate(entries):
            compression = zipfile.ZIP_STORED if position == 0 else zipfile.ZIP_DEFLATED
            target.writestr(zipfile.ZipInfo(name), payload, compress_type=compression)
    return path


def _repacked(tmp_path: Path, mutate) -> Path:
    entries = _entries(_write_archive(tmp_path / "source.urch"))
    return _pack(tmp_path / "repacked.urch", mutate(entries))


def test_the_marker_entry_comes_first_and_is_not_compressed(tmp_path):
    """Несжатая первая запись кладёт сигнатуру в фиксированное смещение: тип файла узнаётся по
    содержимому, а не по расширению, — иначе от переименованного zip архив ничем не отличить."""
    path = _write_archive(tmp_path / "a.urch")
    with zipfile.ZipFile(path) as raw:
        assert raw.namelist()[0] == MIMETYPE_ENTRY
        assert raw.getinfo(MIMETYPE_ENTRY).compress_type == zipfile.ZIP_STORED
        assert raw.read(MIMETYPE_ENTRY).decode("utf-8") == ARCHIVE_MEDIA_TYPE


def test_rows_and_bodies_come_back_exactly_as_written(tmp_path):
    path = _write_archive(tmp_path / "a.urch")
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        assert reader.rows(ENTITY_RESEARCH) == [RESEARCH_ROW]
        assert reader.rows(ENTITY_NOTES) == [NOTE_ROW]
        assert reader.body(ENTITY_RESEARCH, RESEARCH_CODE) == BODY
        assert reader.page_material(PAGE_CODE) == MATERIAL


def test_the_manifest_lists_every_written_entry(tmp_path):
    path = _write_archive(tmp_path / "a.urch")
    with ArchiveReader(path) as reader:
        manifest = reader.open_manifest()
    assert {item.path for item in manifest.files} == {
        rows_entry(ENTITY_RESEARCH),
        rows_entry(ENTITY_NOTES),
        body_entry(ENTITY_RESEARCH, RESEARCH_CODE),
        page_material_entry(PAGE_CODE),
    }


def test_a_rows_entry_that_was_never_written_reads_as_an_empty_list(tmp_path):
    path = _write_archive(tmp_path / "a.urch")
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        assert reader.rows(ENTITY_AREAS) == []


def test_a_record_without_a_body_reads_as_an_empty_string(tmp_path):
    path = _write_archive(tmp_path / "a.urch")
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        assert reader.body(ENTITY_NOTES, NOTE_CODE) == ""


def test_a_page_without_material_reads_as_nothing(tmp_path):
    """Пустой материал и отсутствующий — разные вещи: первый ложится в базу, второй оставляет
    страницу ждать закачки."""
    path = _write_archive(tmp_path / "a.urch")
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        assert reader.page_material("cd" * 11) is None


def test_verify_inventory_passes_on_an_intact_archive(tmp_path):
    path = _write_archive(tmp_path / "a.urch")
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        reader.verify_inventory()


def test_verify_inventory_catches_an_altered_entry(tmp_path):
    """Сумма записи — единственное, что отличает правленый архив от доехавшего целым."""

    def tamper(entries):
        return [
            (name, b"# not what the manifest promised\n" if name.endswith(".md") else payload)
            for name, payload in entries
        ]

    path = _repacked(tmp_path, tamper)
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        with pytest.raises(ArchiveError, match="повреждена при передаче"):
            reader.verify_inventory()


def test_verify_inventory_catches_an_entry_of_the_same_size(tmp_path):
    """Подмена байт в байт по длине проходит мимо проверки размера — ловит её только sha256."""
    replacement = "y" * len(BODY.encode("utf-8"))

    def tamper(entries):
        return [
            (name, replacement.encode("utf-8") if name == body_entry(ENTITY_RESEARCH, RESEARCH_CODE) else payload)
            for name, payload in entries
        ]

    path = _repacked(tmp_path, tamper)
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        with pytest.raises(ArchiveError, match="повреждена при передаче"):
            reader.verify_inventory()


def test_verify_inventory_catches_an_extra_entry(tmp_path):
    """Запись, которой нет в манифесте, — чужая: она легла бы в базу, никем не подписанная."""
    smuggled = body_entry(ENTITY_NOTES, NOTE_CODE)
    path = _repacked(tmp_path, lambda entries: entries + [(smuggled, b"# smuggled\n")])
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        with pytest.raises(ArchiveError, match=f"лишнее: {smuggled}"):
            reader.verify_inventory()


def test_verify_inventory_catches_a_missing_entry(tmp_path):
    dropped = body_entry(ENTITY_RESEARCH, RESEARCH_CODE)
    path = _repacked(tmp_path, lambda entries: [e for e in entries if e[0] != dropped])
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        with pytest.raises(ArchiveError, match=f"нет: {dropped}"):
            reader.verify_inventory()


@pytest.mark.parametrize(
    "name",
    [
        "../evil.md",
        "rows/unknown.jsonl",
        "rows/research.json",
        f"bodies/notes/{NOTE_CODE}.txt",
        "bodies/notes/zzzzzzzzzz.md",
        f"bodies/notes/{NOTE_CODE}0.md",
        "bodies/unknown/0123456789.md",
        f"pages/{RESEARCH_CODE}.md",
        "readme.txt",
    ],
    ids=[
        "escape", "unknown-entity", "wrong-suffix", "body-not-md", "body-not-hex",
        "body-too-long", "unknown-body-directory", "page-code-too-short", "stray-file",
    ],
)
def test_an_entry_outside_the_layout_is_refused(tmp_path, name):
    """Имя записи участвует в сопоставлении «тело ↔ строка», поэтому разрешены ровно те формы,
    которые пишет экспорт: `..` в пути — лишь один из способов испортить разбор."""
    path = _repacked(tmp_path, lambda entries: entries + [(name, b"whatever")])
    with ArchiveReader(path) as reader:
        with pytest.raises(ArchiveError, match="недопустимую запись"):
            reader.open_manifest()


def test_an_archive_without_the_marker_is_refused(tmp_path):
    path = _repacked(tmp_path, lambda entries: [e for e in entries if e[0] != MIMETYPE_ENTRY])
    with ArchiveReader(path) as reader:
        with pytest.raises(ArchiveError, match="не является архивом .urch"):
            reader.open_manifest()


def test_an_archive_whose_marker_is_not_first_is_refused(tmp_path):
    """Смещение сигнатуры — весь смысл опознавательной записи: не первая — значит не наша."""
    path = _repacked(tmp_path, lambda entries: entries[1:] + entries[:1])
    with ArchiveReader(path) as reader:
        with pytest.raises(ArchiveError, match="не является архивом .urch"):
            reader.open_manifest()


def test_a_marker_holding_a_foreign_media_type_is_refused(tmp_path):
    def tamper(entries):
        return [
            (name, b"application/epub+zip" if name == MIMETYPE_ENTRY else payload)
            for name, payload in entries
        ]

    path = _repacked(tmp_path, tamper)
    with ArchiveReader(path) as reader:
        with pytest.raises(ArchiveError, match="не является архивом .urch"):
            reader.open_manifest()


def test_an_archive_without_a_manifest_is_refused(tmp_path):
    path = _repacked(tmp_path, lambda entries: [e for e in entries if e[0] != MANIFEST_ENTRY])
    with ArchiveReader(path) as reader:
        with pytest.raises(ArchiveError, match="нет манифеста"):
            reader.open_manifest()


def test_a_broken_manifest_inside_a_valid_container_is_refused(tmp_path):
    def tamper(entries):
        return [
            (name, b"{" if name == MANIFEST_ENTRY else payload) for name, payload in entries
        ]

    path = _repacked(tmp_path, tamper)
    with ArchiveReader(path) as reader:
        with pytest.raises(ArchiveError, match="повреждён или не читается"):
            reader.open_manifest()


@pytest.mark.parametrize("payload", [b"", b"just text, not a zip"], ids=["empty", "text"])
def test_a_file_that_is_not_a_zip_is_refused(tmp_path, payload):
    path = tmp_path / "a.urch"
    path.write_bytes(payload)
    with pytest.raises(ArchiveError, match="не является архивом .urch"):
        with ArchiveReader(path):
            pass


def test_reading_before_the_archive_is_opened_is_refused(tmp_path):
    with pytest.raises(ArchiveError, match="архив не открыт"):
        ArchiveReader(_write_archive(tmp_path / "a.urch")).rows(ENTITY_RESEARCH)


def test_an_oversized_entry_is_caught_while_reading_and_not_by_the_zip_header(
    tmp_path, monkeypatch
):
    """Заголовок zip — часть того же недоверенного файла, и сжатый объём о распакованном ничего
    не говорит: предел обязан срабатывать на прочитанных байтах."""
    limit = 4096
    inflated = "a" * (limit * 16)
    path = tmp_path / "bomb.urch"
    with ArchiveWriter(path) as writer:
        writer.add_body(ENTITY_RESEARCH, RESEARCH_CODE, inflated)
        writer.finish(
            archive_id="01JB0000000000000000000000",
            source=ManifestSource(),
            roots=[ManifestRoot(type=ENTITY_RESEARCH, code=RESEARCH_CODE, title="Исследование")],
            counts={},
            dangling_refs=[],
        )
    with zipfile.ZipFile(path) as raw:
        assert raw.getinfo(body_entry(ENTITY_RESEARCH, RESEARCH_CODE)).compress_size < limit

    monkeypatch.setattr(archive_module, "MAX_ENTRY_BYTES", limit)
    with ArchiveReader(path) as reader:
        reader.open_manifest()
        with pytest.raises(ArchiveError, match="превышает предел распаковки"):
            reader.body(ENTITY_RESEARCH, RESEARCH_CODE)


def test_check_total_size_refuses_an_archive_over_the_limit(tmp_path, monkeypatch):
    path = _write_archive(tmp_path / "a.urch")
    monkeypatch.setattr(archive_module, "MAX_TOTAL_UNCOMPRESSED_BYTES", 10)
    with pytest.raises(ArchiveError, match="не проходит по пределам распаковки"):
        check_total_size(path)


def test_check_total_size_passes_an_ordinary_archive(tmp_path):
    check_total_size(_write_archive(tmp_path / "a.urch"))


def test_uncompressed_size_counts_the_unpacked_bytes(tmp_path):
    path = _write_archive(tmp_path / "a.urch")
    with zipfile.ZipFile(path) as raw:
        expected = sum(len(raw.read(name)) for name in raw.namelist())
    assert uncompressed_size(path) == expected


def test_the_manifest_sums_match_the_written_bytes(tmp_path):
    """Сумма считается на лету при записи: разъехавшись с содержимым, она обвинила бы в порче
    канал передачи там, где ошибся сам экспорт."""
    path = _write_archive(tmp_path / "a.urch")
    with ArchiveReader(path) as reader:
        manifest = reader.open_manifest()
    with zipfile.ZipFile(path) as raw:
        for item in manifest.files:
            payload = raw.read(item.path)
            assert item.bytes == len(payload)
            assert item.sha256 == hashlib.sha256(payload).hexdigest()


def test_rows_are_written_one_json_object_per_line(tmp_path):
    """Построчный формат читается и дописывается потоком — на нём стоит весь разбор строк."""
    path = _write_archive(tmp_path / "a.urch")
    with zipfile.ZipFile(path) as raw:
        lines = raw.read(rows_entry(ENTITY_RESEARCH)).decode("utf-8").splitlines()
    assert [json.loads(line) for line in lines] == [RESEARCH_ROW]
