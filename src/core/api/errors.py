"""Стандартные ошибки API.

Единый формат тела ошибки для любого не-2xx ответа: ``{error, code?, fields?}``.
Успех остаётся «телом как есть» — стандартизируем только ошибки (статус-код —
источник истины об успехе/неуспехе).

Модули кидают ``ApiError`` (через удобные конструкторы), общий handler
(``register_exception_handlers``) превращает её в ``ErrorBody`` + HTTP-статус.
"""

from __future__ import annotations

from pydantic import BaseModel


class ErrorBody(BaseModel):
    """Тело любого не-2xx ответа API."""

    error: str                                # человекочитаемое сообщение
    code: str | None = None                   # машинный код для кода-обработчика на клиенте
    fields: dict[str, str] | None = None      # ошибки по полям (валидация форм)


class ApiError(Exception):
    """Бизнес-ошибка API. Перехватывается общим handler'ом → ErrorBody + status_code.

    Использовать конструкторы по статусам (``ApiError.not_found(...)`` и т.п.),
    а не собирать вручную — так статус и семантика не разъезжаются.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: str | None = None,
        fields: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.fields = fields

    def body(self) -> ErrorBody:
        return ErrorBody(error=self.message, code=self.code, fields=self.fields)

    # ── конструкторы по статусам ─────────────────────────────────────────
    @classmethod
    def bad_request(cls, message: str = "Некорректный запрос", *, code: str | None = None,
                    fields: dict[str, str] | None = None) -> "ApiError":
        return cls(400, message, code=code, fields=fields)

    @classmethod
    def unauthorized(cls, message: str = "Требуется авторизация", *, code: str | None = None) -> "ApiError":
        return cls(401, message, code=code)

    @classmethod
    def forbidden(cls, message: str = "Недостаточно прав", *, code: str | None = None) -> "ApiError":
        return cls(403, message, code=code)

    @classmethod
    def not_found(cls, message: str = "Не найдено", *, code: str | None = None) -> "ApiError":
        return cls(404, message, code=code)

    @classmethod
    def conflict(cls, message: str = "Конфликт", *, code: str | None = None,
                 fields: dict[str, str] | None = None) -> "ApiError":
        return cls(409, message, code=code, fields=fields)

    @classmethod
    def validation(cls, message: str = "Ошибка валидации", *, fields: dict[str, str] | None = None,
                   code: str | None = "validation_error") -> "ApiError":
        return cls(422, message, code=code, fields=fields)

    @classmethod
    def too_many_requests(cls, message: str = "Слишком много запросов", *, code: str | None = None) -> "ApiError":
        return cls(429, message, code=code)


__all__ = ["ApiError", "ErrorBody"]
