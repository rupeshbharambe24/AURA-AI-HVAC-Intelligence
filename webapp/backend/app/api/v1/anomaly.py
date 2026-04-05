from __future__ import annotations

import io
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from ...schemas.anomaly import (
    AnomalyBatchResponse,
    AnomalyDetectRequest,
    AnomalyDetectResponse,
    AnomalyMetricsResponse,
    AnomalyOptionsResponse,
    AnomalyThresholds,
)
from ...schemas.jobs import JobStatusResponse
from ...services.inference.anomaly_service import AnomalyService


router = APIRouter()


@router.get("/anomaly/options", response_model=AnomalyOptionsResponse)
def anomaly_options(request: Request) -> AnomalyOptionsResponse:
    service = AnomalyService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    data = service.get_options()
    return AnomalyOptionsResponse(
        **data,
        request_id=request.state.request_id,
    )


@router.post("/anomaly/detect", response_model=AnomalyDetectResponse)
def anomaly_detect(payload: AnomalyDetectRequest, request: Request) -> AnomalyDetectResponse:
    service = AnomalyService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    thresholds = payload.thresholds.model_dump() if payload.thresholds else None
    try:
        data, warnings = service.detect(
            product_id=payload.product_id,
            aps=payload.aps,
            date_range=payload.date_range,
            thresholds=thresholds,
            threshold=payload.threshold,
            include_explanations=payload.include_explanations,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    data["effective_thresholds"] = AnomalyThresholds(**data["effective_thresholds"])
    return AnomalyDetectResponse(
        **data,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.post("/anomaly/batch", response_model=AnomalyBatchResponse)
def anomaly_batch(
    request: Request,
    file: UploadFile = File(...),
    threshold: Optional[float] = None,
):
    service = AnomalyService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )

    raw = file.file.read()
    df = pd.read_csv(io.BytesIO(raw))

    warnings: List[str] = []

    if "product_id" not in df.columns and "product" in df.columns:
        df = df.rename(columns={"product": "product_id"})
    if "demand" not in df.columns and "value" in df.columns:
        df = df.rename(columns={"value": "demand"})

    if "aps" not in df.columns:
        df["aps"] = "ALL"
        warnings.append("aps missing; defaulted to ALL")

    required = {"product_id", "aps", "date", "demand"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(sorted(missing))}")

    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()

    if len(df) <= 5000:
        results, w = service.detect_batch(df, thresholds=None, threshold=threshold, include_explanations=True)
        warnings.extend(w)
        return AnomalyBatchResponse(
            results=results,
            warnings=warnings,
            request_id=request.state.request_id,
        )

    job_manager = request.app.state.job_manager
    job = job_manager.create()

    def _run():
        results, w = service.detect_batch(df, thresholds=None, threshold=threshold, include_explanations=True)
        return {"results": results, "warnings": warnings + w}

    job_manager.run(job, _run)
    return AnomalyBatchResponse(
        job_id=job.job_id,
        status=job.status,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/anomaly/metrics", response_model=AnomalyMetricsResponse)
def anomaly_metrics(request: Request) -> AnomalyMetricsResponse:
    service = AnomalyService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )
    data, warnings = service.get_model_metrics()
    return AnomalyMetricsResponse(
        **data,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str, request: Request) -> JobStatusResponse:
    job = request.app.state.job_manager.get(job_id)
    if not job:
        return JobStatusResponse(
            job_id=job_id,
            status="not_found",
            progress=0.0,
            result=None,
            error="job_id not found",
            request_id=request.state.request_id,
        )
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        result=job.result,
        error=job.error,
        request_id=request.state.request_id,
    )
