from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


async def api_error_handler(request: Request, error: ApiError) -> JSONResponse:
    payload: dict[str, Any] = {
        "code": error.code,
        "message": error.message,
        "request_id": request.state.request_id,
    }
    if error.details is not None:
        payload["details"] = error.details
    return JSONResponse(status_code=error.status_code, content=payload)
