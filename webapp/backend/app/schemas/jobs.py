from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from .common import BaseResponse


class JobStatusResponse(BaseResponse):
    job_id: str
    status: str
    progress: float
    result: Optional[Any] = None
    error: Optional[str] = None
