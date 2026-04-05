from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    request_id: str = Field(..., description="Request correlation id")


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str
    details: Optional[Any] = None
