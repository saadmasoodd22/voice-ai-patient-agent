from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"data": data, "error": None})


def fail(message: str, status_code: int, code: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "error": {"message": message, "code": code or str(status_code)},
        },
    )


def serialize(model) -> dict:
    return model.model_dump(mode="json")
