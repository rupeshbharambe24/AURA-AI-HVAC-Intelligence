from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from ...schemas.health import HealthMetricsResponse, HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        version=settings.VERSION,
        time_utc=datetime.now(timezone.utc).isoformat(),
        request_id=request.state.request_id,
    )


@router.get("/health/metrics", response_model=HealthMetricsResponse)
def health_metrics(request: Request) -> HealthMetricsResponse:
    metrics = request.app.state.metrics
    total = metrics.get("count", 0) or 0
    error_count = metrics.get("error_count", 0) or 0
    latency_sum = metrics.get("latency_sum", 0.0) or 0.0

    api_latency_ms = (latency_sum / total) if total else 0.0
    error_rate_pct = (error_count / total * 100.0) if total else 0.0

    registry = request.app.state.registry_service
    models, _ = registry.list_models()
    models_in_prod = len([m for m in models if m.get("alias") == "prod"])

    return HealthMetricsResponse(
        api_latency_ms=round(api_latency_ms, 2),
        error_rate_pct=round(error_rate_pct, 2),
        uptime_pct=100.0,
        active_jobs=0,
        drift_detected=False,
        models_in_prod=models_in_prod,
        request_id=request.state.request_id,
    )
