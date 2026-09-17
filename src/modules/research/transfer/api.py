"""Ручки переноса: выгрузка архива и три шага импорта (загрузка → разбор → применение).

Шаги разведены не для красоты: пока человек смотрит на план, в базе ничего не меняется, а
разбор и применение — разные ручки с разными правами на запись. Отмена уносит временный файл,
чтобы брошенный заход не оставлял мусора до суточной уборки.
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask
from ulid import ULID

from src.core.api import ApiError
from src.modules.research.codes import strip_prefix
from src.modules.research.crud import research as research_crud
from src.modules.research.transfer.constants import (
    ARCHIVE_EXTENSION,
    ARCHIVE_MEDIA_TYPE,
    IMPORT_MODE_NEWER,
    IMPORT_MODES,
)
from src.modules.research.transfer.errors import ArchiveError
from src.modules.research.transfer.export import export_research
from src.modules.research.transfer.ingest import ImportReport
from src.modules.research.transfer.plan import ImportPlan
from src.modules.research.transfer.runner import analyze_archive, import_archive
from src.modules.research.transfer import uploads

router = APIRouter()


class UploadedArchive(BaseModel):
    """Что вернулось после загрузки файла: чем его звать дальше и что показать человеку."""

    upload_id: str
    file_name: str
    size: int


class ArchivePassport(BaseModel):
    """Шапка плана: что за файл и откуда он приехал."""

    file_name: str
    size: int
    created_at: str
    app_version: str
    format_version: int
    same_install: bool


class RootRef(BaseModel):
    code: str
    title: str


class PlanWarningsBody(BaseModel):
    """Все четыре корзины присутствуют всегда — пустая корзина это ``[]``, а не отсутствие поля."""

    dangling_refs: list[str] = Field(default_factory=list)
    diverged_pages: list[dict[str, str]] = Field(default_factory=list)
    locally_newer: list[dict[str, str]] = Field(default_factory=list)
    truncated: list[dict[str, str]] = Field(default_factory=list)


class ImportPlanBody(BaseModel):
    archive: ArchivePassport
    roots: list[RootRef]
    counts: dict[str, dict[str, int]]
    details: dict[str, list[dict[str, str]]]
    warnings: PlanWarningsBody


class ImportReportBody(BaseModel):
    roots: list[RootRef]
    counts: dict[str, dict[str, int]]
    refs_rewritten: int
    dangling_refs: list[str]
    warnings: PlanWarningsBody


class ImportModeBody(BaseModel):
    """Что делать с записью, которая в базе уже есть."""

    mode: str = IMPORT_MODE_NEWER


@router.get("/researches/{code}/export")
async def export_archive(code: str) -> FileResponse:
    """Собрать архив исследования и отдать файлом с именем-названием."""
    research_code = strip_prefix(code)
    if await research_crud.research_get(research_code) is None:
        raise ApiError.not_found("Исследование не найдено")

    path = uploads.export_directory() / f"{ULID()}{ARCHIVE_EXTENSION}"
    archive = await export_research(research_code, path)
    return FileResponse(
        path=archive.path,
        media_type=ARCHIVE_MEDIA_TYPE,
        filename=archive.file_name,
        background=BackgroundTask(uploads.drop_export, archive.path),
    )


@router.post("/import/upload")
async def upload_archive(file: UploadFile = File()) -> UploadedArchive:
    """Принять файл во временную папку — первый из трёх шагов импорта."""
    try:
        stored = await uploads.store_upload(file)
    except ArchiveError as error:
        raise ApiError.bad_request(str(error)) from error
    return UploadedArchive(
        upload_id=stored.upload_id, file_name=stored.file_name, size=stored.size
    )


@router.post("/import/{upload_id}/analyze")
async def analyze_upload(upload_id: str, body: ImportModeBody | None = None) -> ImportPlanBody:
    """Разобрать загруженный архив и показать план; базу не трогает."""
    mode = _checked_mode(body)
    stored = _stored(upload_id)
    try:
        plan = await analyze_archive(stored.path, mode=mode)
    except ArchiveError as error:
        raise ApiError.bad_request(str(error)) from error
    return _plan_body(plan, stored)


@router.post("/import/{upload_id}/apply")
async def apply_upload(upload_id: str, body: ImportModeBody | None = None) -> ImportReportBody:
    """Применить архив к базе и отдать отчёт."""
    mode = _checked_mode(body)
    stored = _stored(upload_id)
    try:
        plan, report = await import_archive(stored.path, mode=mode)
    except ArchiveError as error:
        raise ApiError.bad_request(str(error)) from error
    uploads.drop_upload(upload_id)
    return _report_body(plan, report)


@router.delete("/import/{upload_id}", status_code=204)
async def cancel_upload(upload_id: str) -> None:
    """Отменить заход: временный файл уходит сразу, не дожидаясь суточной уборки."""
    uploads.drop_upload(upload_id)


def _checked_mode(body: ImportModeBody | None) -> str:
    mode = (body or ImportModeBody()).mode
    if mode not in IMPORT_MODES:
        raise ApiError.validation(
            f"Неизвестный режим импорта «{mode}»", fields={"mode": "|".join(IMPORT_MODES)}
        )
    return mode


def _stored(upload_id: str) -> uploads.StoredUpload:
    try:
        return uploads.upload_info(upload_id)
    except ArchiveError as error:
        raise ApiError.not_found(str(error)) from error


def _plan_body(plan: ImportPlan, stored: uploads.StoredUpload) -> ImportPlanBody:
    return ImportPlanBody(
        archive=ArchivePassport(
            file_name=stored.file_name,
            size=stored.size,
            created_at=plan.manifest.created_at,
            app_version=plan.manifest.source.app_version,
            format_version=plan.manifest.format_version,
            same_install=plan.same_install,
        ),
        roots=[RootRef(**root) for root in plan.root_codes()],
        counts=plan.counts(),
        details=plan.details(),
        warnings=_warnings_body(plan),
    )


def _report_body(plan: ImportPlan, report: ImportReport) -> ImportReportBody:
    return ImportReportBody(
        roots=[RootRef(**root) for root in report.roots],
        counts=report.counts,
        refs_rewritten=report.refs_rewritten,
        dangling_refs=report.dangling_refs,
        warnings=_warnings_body(plan, truncated=report.truncated),
    )


def _warnings_body(
    plan: ImportPlan, *, truncated: list[dict[str, str]] | None = None
) -> PlanWarningsBody:
    return PlanWarningsBody(
        dangling_refs=plan.warnings.dangling_refs,
        diverged_pages=plan.warnings.diverged_pages,
        locally_newer=plan.warnings.locally_newer,
        truncated=plan.warnings.truncated if truncated is None else truncated,
    )


__all__ = ["router"]
