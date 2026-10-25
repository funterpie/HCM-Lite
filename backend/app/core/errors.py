from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields or {}
        super().__init__(message)


def _error_body(
    code: str, message: str, fields: Mapping[str, str] | None = None
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields:
        error["fields"] = dict(fields)
    return {"error": error}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message, exc.fields),
    )


async def http_exception_handler(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    status_map = {
        400: ("validation_error", "The request is invalid."),
        401: ("unauthorized", "Authentication is required."),
        403: ("forbidden", "You do not have permission to perform this action."),
        404: ("not_found", "The requested resource was not found."),
        409: ("duplicate", "The request conflicts with an existing record."),
        422: ("rule_violation", "The request could not be processed."),
        429: ("rate_limited", "Too many requests."),
    }
    code, default_message = status_map.get(
        exc.status_code, ("http_error", "The request could not be completed.")
    )
    detail = exc.detail
    message = detail if isinstance(detail, str) else default_message
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code, message),
        headers=exc.headers,
    )


async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    fields: dict[str, str] = {}
    for issue in exc.errors():
        location = ".".join(str(part) for part in issue["loc"] if part != "body")
        fields[location or "request"] = issue["msg"]
    return JSONResponse(
        status_code=400,
        content=_error_body("validation_error", "The request is invalid.", fields),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
