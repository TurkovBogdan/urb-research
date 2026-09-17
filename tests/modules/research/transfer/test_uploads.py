"""Временная папка импорта: уборка брошенных загрузок и отказ по форме идентификатора.

Фонового рабочего в установке может не быть вовсе, поэтому уборка висит на самой загрузке —
и если она молча перестанет работать, диск будет заполняться архивами, которые никто не звал.
"""

from __future__ import annotations

import os
import time

import pytest

from src.modules.research.transfer import uploads
from src.modules.research.transfer.errors import ArchiveError

pytestmark = pytest.mark.pure


@pytest.fixture
def uploads_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "uploads_directory", lambda: tmp_path)
    return tmp_path


def _aged(path, *, days: float) -> None:
    stale = time.time() - days * 24 * 60 * 60
    os.utime(path, (stale, stale))


def test_an_abandoned_upload_is_swept_and_a_fresh_one_is_kept(uploads_dir):
    stale = uploads_dir / "01ARZ3NDEKTSV4RRFFQ69G5FAV.urch"
    stale.write_bytes(b"stale")
    _aged(stale, days=2)
    fresh = uploads_dir / "01BX5ZZKBKACTAV9WEVGEMMVRZ.urch"
    fresh.write_bytes(b"fresh")

    uploads.sweep_stale_uploads()

    assert not stale.exists()
    assert fresh.exists()


def test_the_passport_of_an_abandoned_upload_goes_with_it(uploads_dir):
    """Записка с именем файла обязана уходить вместе с архивом, иначе папка копит хвосты."""
    for name in ("01ARZ3NDEKTSV4RRFFQ69G5FAV.urch", "01ARZ3NDEKTSV4RRFFQ69G5FAV.json"):
        path = uploads_dir / name
        path.write_bytes(b"{}")
        _aged(path, days=2)

    uploads.sweep_stale_uploads()

    assert not list(uploads_dir.iterdir())


@pytest.mark.parametrize(
    "upload_id",
    ["", "../etc/passwd", "01ARZ3NDEKTSV4RRFFQ69G5FA", "01arz3ndektsv4rrffq69g5fav", "evil"],
    ids=["empty", "path", "too-short", "lowercase", "word"],
)
def test_an_identifier_of_a_foreign_shape_never_reaches_the_disk(uploads_dir, upload_id):
    (uploads_dir / f"{upload_id}.urch").parent.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ArchiveError):
        uploads.upload_path(upload_id)


def test_a_well_shaped_identifier_without_a_file_is_refused_too(uploads_dir):
    with pytest.raises(ArchiveError):
        uploads.upload_path("01ARZ3NDEKTSV4RRFFQ69G5FAV")


def test_dropping_an_upload_takes_both_of_its_files(uploads_dir):
    upload_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    (uploads_dir / f"{upload_id}.urch").write_bytes(b"archive")
    (uploads_dir / f"{upload_id}.json").write_text("{}", encoding="utf-8")

    uploads.drop_upload(upload_id)

    assert not list(uploads_dir.iterdir())
