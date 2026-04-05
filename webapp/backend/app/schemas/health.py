from __future__ import annotations

from pydantic import BaseModel

from .common import BaseResponse


class HealthResponse(BaseResponse):
    status: str
    service: str
    version: str
    time_utc: str


class HealthMetricsResponse(BaseResponse):
    api_latency_ms: float
    error_rate_pct: float
    uptime_pct: float
    active_jobs: int
    drift_detected: bool
    models_in_prod: int

