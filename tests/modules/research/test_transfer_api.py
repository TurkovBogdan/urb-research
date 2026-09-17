"""HTTP-поверхность переноса: выгрузка файлом и три шага импорта (загрузка → разбор → применение).

Временные папки уводятся в ``tmp_path``: ручки кладут файл на диск, и тест не вправе оставлять
его в рантайме установки.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.api import register_exception_handlers
from src.core.config import Config
from src.core.database import close_database, init_database
from src.core.database.runtime import Base
from src.modules.research.api import router
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.transfer import uploads
from src.modules.research.transfer.constants import (
    ARCHIVE_MEDIA_TYPE,
    ENTITY_AREAS,
    ENTITY_RESEARCH,
)

pytestmark = pytest.mark.db


@pytest.fixture
async def app(config: Config, tmp_path, monkeypatch):
    engine = await init_database(config)
    import src.modules.research.models  # noqa: F401 — register research tables
    import src.modules.web_search.models  # noqa: F401 — source join target

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(uploads, "uploads_directory", lambda: _made(tmp_path / "import"))
    monkeypatch.setattr(uploads, "export_directory", lambda: _made(tmp_path / "export"))

    fastapi_app = FastAPI()
    register_exception_handlers(fastapi_app)
    fastapi_app.include_router(router, prefix="/internal/research")
    try:
        yield fastapi_app
    finally:
        await close_database()


def _made(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _seed() -> str:
    research = await research_crud.research_create(title="Тема переноса")
    area = await area_crud.area_create(research_code=research.code, title="Область")
    await note_crud.note_create(
        research_code=research.code, kind="result", title="Вывод", body=f"см. AREA@{area.code}"
    )
    return research.code


async def _exported(client) -> tuple[str, bytes]:
    code = await _seed()
    response = await client.get(f"/internal/research/researches/{code}/export")
    assert response.status_code == 200
    return code, response.content


async def test_export_returns_the_archive_named_after_the_research(client):
    code = await _seed()

    response = await client.get(f"/internal/research/researches/RESEARCH@{code}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == ARCHIVE_MEDIA_TYPE
    assert "attachment" in response.headers["content-disposition"]
    assert "urch" in response.headers["content-disposition"]
    assert response.content[:2] == b"PK"


async def test_export_of_an_unknown_research_is_not_found(client):
    response = await client.get("/internal/research/researches/0000000000/export")

    assert response.status_code == 404


async def test_upload_analyze_apply_walks_the_archive_into_the_base(client):
    code, archive = await _exported(client)
    await research_crud.research_delete(code)

    upload = (
        await client.post(
            "/internal/research/import/upload",
            files={"file": ("Тема переноса.urch", archive, ARCHIVE_MEDIA_TYPE)},
        )
    ).json()
    assert upload["file_name"] == "Тема переноса.urch"
    assert upload["size"] == len(archive)

    plan = (
        await client.post(f"/internal/research/import/{upload['upload_id']}/analyze", json={})
    ).json()
    assert plan["archive"]["file_name"] == "Тема переноса.urch"
    assert plan["archive"]["same_install"] is True
    assert plan["counts"][ENTITY_RESEARCH]["create"] == 1
    assert plan["counts"][ENTITY_AREAS]["create"] == 1
    assert set(plan["warnings"]) == {
        "dangling_refs",
        "diverged_pages",
        "locally_newer",
        "truncated",
    }
    assert plan["roots"][0]["title"] == "Тема переноса"

    report = (
        await client.post(
            f"/internal/research/import/{upload['upload_id']}/apply", json={"mode": "newer"}
        )
    ).json()
    assert report["counts"][ENTITY_RESEARCH]["created"] == 1
    assert report["roots"][0]["code"].startswith("RESEARCH@")
    assert await research_crud.research_count() == 1

    spent = await client.post(
        f"/internal/research/import/{upload['upload_id']}/analyze", json={}
    )
    assert spent.status_code == 404


async def test_cancel_removes_the_uploaded_file(client):
    _, archive = await _exported(client)
    upload = (
        await client.post(
            "/internal/research/import/upload",
            files={"file": ("archive.urch", archive, ARCHIVE_MEDIA_TYPE)},
        )
    ).json()

    assert (await client.delete(f"/internal/research/import/{upload['upload_id']}")).status_code == 204

    after = await client.post(
        f"/internal/research/import/{upload['upload_id']}/analyze", json={}
    )
    assert after.status_code == 404


async def test_unknown_mode_is_refused_before_the_archive_is_read(client):
    response = await client.post(
        "/internal/research/import/01ARZ3NDEKTSV4RRFFQ69G5FAV/analyze", json={"mode": "мимо"}
    )

    assert response.status_code == 422
    assert response.json()["fields"]["mode"]


async def _repacked(archive: bytes, mutate) -> bytes:
    """Пересобрать архив, дав тесту переписать его записи, — подделка недоверенного файла."""
    import io
    import zipfile

    source = zipfile.ZipFile(io.BytesIO(archive))
    entries = [(item.filename, source.read(item.filename)) for item in source.infolist()]
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as packed:
        for name, payload in mutate(entries):
            packed.writestr(name, payload)
    return target.getvalue()


async def _refusal(client, archive: bytes) -> dict:
    """Загрузить файл и разобрать его; вернуть тело ответа разбора."""
    upload = (
        await client.post(
            "/internal/research/import/upload",
            files={"file": ("archive.urch", archive, ARCHIVE_MEDIA_TYPE)},
        )
    ).json()
    response = await client.post(
        f"/internal/research/import/{upload['upload_id']}/analyze", json={}
    )
    return {"status": response.status_code, "body": response.json()}


async def test_an_entry_outside_the_layout_is_refused(client):
    """Имя записи — единственное, что архив диктует файловой системе; проверяется до чтения."""
    _, archive = await _exported(client)

    def add_stray(entries):
        return entries + [("../evil.md", b"payload")]

    refusal = await _refusal(client, await _repacked(archive, add_stray))

    assert refusal["status"] == 400
    assert "evil" in refusal["body"]["error"]
    assert await research_crud.research_count() == 1


async def test_a_tampered_entry_is_caught_by_its_checksum(client):
    """Подмена равной длины проходит все проверки, кроме суммы, — ради неё сумма и считается."""
    _, archive = await _exported(client)

    def swap_body(entries):
        return [
            (name, b"X" * len(payload) if name.startswith("bodies/") else payload)
            for name, payload in entries
        ]

    refusal = await _refusal(client, await _repacked(archive, swap_body))

    assert refusal["status"] == 400
    assert "повреждена" in refusal["body"]["error"]


async def test_an_archive_from_a_newer_format_is_refused_by_version(client):
    _, archive = await _exported(client)

    def bump_version(entries):
        import json

        return [
            (
                name,
                json.dumps({**json.loads(payload), "format_version": 99}).encode()
                if name == "manifest.json"
                else payload,
            )
            for name, payload in entries
        ]

    refusal = await _refusal(client, await _repacked(archive, bump_version))

    assert refusal["status"] == 400
    assert "более новой версией формата" in refusal["body"]["error"]


async def test_a_file_over_the_limit_is_refused_while_it_uploads(client, monkeypatch):
    """Предел считается по прочитанным байтам: отказ приходит, не дождавшись конца файла."""
    monkeypatch.setattr(uploads, "MAX_UPLOAD_BYTES", 1024)

    response = await client.post(
        "/internal/research/import/upload",
        files={"file": ("big.urch", b"0" * 4096, ARCHIVE_MEDIA_TYPE)},
    )

    assert response.status_code == 400
    assert not list(uploads.uploads_directory().glob("*.urch"))


async def test_an_upload_id_of_a_foreign_shape_is_refused_even_when_the_file_exists(client):
    """Идентификатор участвует в пути, поэтому проверяется его **форма**, а не наличие файла.

    Файл кладётся во временную папку заранее и под годным именем: проверка «а есть ли такой
    файл» пропустила бы его, и тест бы этого не заметил.
    """
    _, archive = await _exported(client)
    (uploads.uploads_directory() / "evil.urch").write_bytes(archive)

    response = await client.post("/internal/research/import/evil/analyze", json={})

    assert response.status_code == 404


async def test_applying_a_broken_archive_refuses_without_writing(client):
    """Применение зовут и без разбора — свои проверки у него те же, и отказ такой же читаемый."""
    _, archive = await _exported(client)

    def swap_body(entries):
        return [
            (name, b"X" * len(payload) if name.startswith("bodies/") else payload)
            for name, payload in entries
        ]

    upload = (
        await client.post(
            "/internal/research/import/upload",
            files={"file": ("archive.urch", await _repacked(archive, swap_body), ARCHIVE_MEDIA_TYPE)},
        )
    ).json()

    response = await client.post(
        f"/internal/research/import/{upload['upload_id']}/apply", json={"mode": "newer"}
    )

    assert response.status_code == 400
    assert "повреждена" in response.json()["error"]
    assert await research_crud.research_count() == 1


async def test_a_foreign_file_is_refused_with_a_readable_message(client):
    upload = (
        await client.post(
            "/internal/research/import/upload",
            files={"file": ("notes.urch", b"not an archive at all", ARCHIVE_MEDIA_TYPE)},
        )
    ).json()

    response = await client.post(
        f"/internal/research/import/{upload['upload_id']}/analyze", json={}
    )

    assert response.status_code == 400
    assert "urch" in response.json()["error"]
