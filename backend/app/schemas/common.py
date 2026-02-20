from pydantic import BaseModel
from typing import Any, Optional

class ErrorResponse(BaseModel):
    code: str
    message: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorResponse] = None

def ok(data):
    return APIResponse(success=True, data=data, error=None)

def fail(code: str, message: str):
    return APIResponse(success=False, data=None, error=ErrorResponse(code=code, message=message))
