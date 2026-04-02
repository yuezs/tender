from typing import Any


def success_response(data: Any, message: str = "ok") -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(message: str, data: Any | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "data": data if data is not None else {},
    }
