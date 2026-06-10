from fastapi.responses import JSONResponse
from typing import Any

def success_response(data: Any = None, message: str = "Succès", code: int = 200):
    return JSONResponse(status_code=code, content={
        "code": code,
        "message": message,
        "data": data
    })

def error_response(message: str, code: int = 400, data: Any = None):
    return JSONResponse(status_code=code, content={
        "code": code,
        "message": message,
        "data": data
    })
