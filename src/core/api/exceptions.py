"""Единые exception-handler'ы: любой нативный «зоопарк» FastAPI → ``ErrorBody``.

Сводит к одному формату ``{error, code?, fields?}``:
- ``ApiError``               — наш бизнес-класс (несёт status/code/fields);
- ``HTTPException``          — голый ``raise HTTPException(404, "...")`` по модулям
                               (detail-строка → ``error``; detail-объект → message/code);
- ``RequestValidationError`` — 422 от Pydantic (список → ``fields``);
- ``Exception``              — необработанное → 500 (логируем, наружу — нейтральный текст).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.api.errors import ApiError, ErrorBody
from src.core.loggers import get_logger

_LOG = get_logger()


def _json(status_code: int, body: ErrorBody) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Повесить общие обработчики ошибок на приложение (вызывать в create_app)."""

    @app.exception_handler(ApiError)
    async def _on_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _json(exc.status_code, exc.body())

    @app.exception_handler(StarletteHTTPException)
    async def _on_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict):
            message = str(detail.get("error") or detail.get("message") or detail)
            code = detail.get("code")
            fields = detail.get("fields") if isinstance(detail.get("fields"), dict) else None
            body = ErrorBody(error=message, code=code, fields=fields)
        else:
            body = ErrorBody(error=str(detail))
        return _json(exc.status_code, body)

    @app.exception_handler(RequestValidationError)
    async def _on_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for err in exc.errors():
            # loc = ("body"/"query"/"path", <поле>, ...) — отбрасываем источник.
            parts = [str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path")]
            key = ".".join(parts) or "_"
            fields.setdefault(key, err.get("msg", "invalid"))
        body = ErrorBody(error="Ошибка валидации", code="validation_error", fields=fields)
        return _json(422, body)

    @app.exception_handler(Exception)
    async def _on_unhandled(request: Request, exc: Exception) -> JSONResponse:
        _LOG.exception(
            "unhandled error on %s %s: %s", request.method, request.url.path, exc
        )
        return _json(500, ErrorBody(error="Внутренняя ошибка сервера", code="internal_error"))


__all__ = ["register_exception_handlers"]
