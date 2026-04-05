from __future__ import annotations

from fastapi import APIRouter, Request

from ...schemas.forecast import (
    ForecastModelMetricsResponse,
    ForecastOptionsResponse,
    ForecastRequest,
    ForecastResponse,
)
from ...services.inference.forecast_service import ForecastService


router = APIRouter()


@router.get("/forecast/options", response_model=ForecastOptionsResponse)
def forecast_options(request: Request) -> ForecastOptionsResponse:
    service = ForecastService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    data = service.get_options()
    return ForecastOptionsResponse(
        **data,
        request_id=request.state.request_id,
    )


@router.post("/forecast/predict", response_model=ForecastResponse)
def forecast_predict(payload: ForecastRequest, request: Request) -> ForecastResponse:
    service = ForecastService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    data, warnings = service.predict(
        product_id=payload.product_id,
        aps=payload.aps,
        horizon_months=payload.horizon_months,
        cutoff_date=payload.cutoff_date,
        scenarios=payload.scenarios,
        include_actuals=payload.include_actuals,
        include_explain=payload.include_explain,
    )
    return ForecastResponse(
        **data,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/forecast/metrics", response_model=ForecastModelMetricsResponse)
def forecast_metrics(request: Request) -> ForecastModelMetricsResponse:
    service = ForecastService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    data, warnings = service.get_model_metrics()
    return ForecastModelMetricsResponse(
        **data,
        warnings=warnings,
        request_id=request.state.request_id,
    )
