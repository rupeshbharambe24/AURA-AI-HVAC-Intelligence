from __future__ import annotations

import io
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from ...schemas.market_share import (
    MarketShareBatchResponse,
    MarketShareMetricsResponse,
    MarketShareOptionsResponse,
    MarketShareRequest,
    MarketShareResponse,
)
from ...services.inference.market_share_service import MarketShareService


router = APIRouter()


@router.get("/market-share/options", response_model=MarketShareOptionsResponse)
def market_share_options(request: Request) -> MarketShareOptionsResponse:
    service = MarketShareService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    data = service.get_options()
    return MarketShareOptionsResponse(**data, request_id=request.state.request_id)


@router.post("/market-share/predict", response_model=MarketShareResponse)
def market_share_predict(payload: MarketShareRequest, request: Request) -> MarketShareResponse:
    service = MarketShareService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    try:
        data, warnings = service.predict(
            product_id=payload.product_id,
            horizon_months=payload.horizon_months,
            as_of_date=payload.as_of_date,
            news_filters=payload.news_filters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return MarketShareResponse(
        **data,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.post("/market-share/batch", response_model=MarketShareBatchResponse)
def market_share_batch(
    request: Request,
    file: UploadFile = File(...),
):
    service = MarketShareService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )

    raw = file.file.read()
    df = pd.read_csv(io.BytesIO(raw))
    warnings: List[str] = []

    if "product_id" not in df.columns and "product" in df.columns:
        df = df.rename(columns={"product": "product_id"})

    required = {"product_id", "horizon_months"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(sorted(missing))}")

    if "as_of_date" not in df.columns:
        df["as_of_date"] = None

    if len(df) <= 5000:
        results, w = service.predict_batch(df)
        warnings.extend(w)
        return MarketShareBatchResponse(
            results=results,
            warnings=warnings,
            request_id=request.state.request_id,
        )

    job_manager = request.app.state.job_manager
    job = job_manager.create()

    def _run():
        results, w = service.predict_batch(df)
        return {"results": results, "warnings": warnings + w}

    job_manager.run(job, _run)
    return MarketShareBatchResponse(
        job_id=job.job_id,
        status=job.status,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/market-share/metrics", response_model=MarketShareMetricsResponse)
def market_share_metrics(request: Request) -> MarketShareMetricsResponse:
    service = MarketShareService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    data, warnings = service.get_model_metrics()
    return MarketShareMetricsResponse(
        **data,
        warnings=warnings,
        request_id=request.state.request_id,
    )
