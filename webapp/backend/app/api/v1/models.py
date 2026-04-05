from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from ...schemas.models import (
    DatasetRowsResponse,
    DatasetTimeseriesResponse,
    DatasetsResponse,
    ModelDetailResponse,
    ModelExplainabilityResponse,
    ModelListResponse,
    ModelMetricsResponse,
    ModelVersionsResponse,
)


router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
def list_models(request: Request) -> ModelListResponse:
    registry = request.app.state.registry_service
    models, warnings = registry.list_models()
    return ModelListResponse(
        models=models,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/models/datasets", response_model=DatasetsResponse)
def list_datasets(request: Request) -> DatasetsResponse:
    repo = request.app.state.data_repo
    datasets = []
    warnings = []
    try:
        for path in repo.list_datasets():
            try:
                df = repo.load_dataset_df(path.name)
                rows = int(len(df))
                cols = int(len(df.columns))
                missingness = float(df.isna().mean().mean() * 100.0) if rows and cols else 0.0
                quality = float(max(0.0, 100.0 - missingness))
                datasets.append(
                    {
                        "name": path.name,
                        "rows": rows,
                        "cols": cols,
                        "lastUpdated": path.stat().st_mtime,
                        "quality": round(quality, 1),
                        "missingness": round(missingness, 1),
                    }
                )
            except Exception as exc:
                warnings.append(f"dataset '{path.name}' skipped: {exc}")
    except Exception as exc:
        warnings.append(str(exc))

    for d in datasets:
        try:
            d["lastUpdated"] = pd.to_datetime(d["lastUpdated"], unit="s").strftime("%Y-%m-%d")
        except Exception:
            d["lastUpdated"] = None

    return DatasetsResponse(datasets=datasets, warnings=warnings, request_id=request.state.request_id)


@router.get("/models/datasets/{name}", response_model=DatasetRowsResponse)
def get_dataset(name: str, request: Request) -> DatasetRowsResponse:
    repo = request.app.state.data_repo
    try:
        rows = repo.get_dataset_rows(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"dataset '{name}' not found")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return DatasetRowsResponse(name=name, rows=rows, request_id=request.state.request_id)


@router.get("/models/datasets/{name}/timeseries", response_model=DatasetTimeseriesResponse)
def get_dataset_timeseries(name: str, request: Request, metric: str | None = None) -> DatasetTimeseriesResponse:
    repo = request.app.state.data_repo
    try:
        series = repo.get_dataset_timeseries(name, metric=metric)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"dataset '{name}' not found")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return DatasetTimeseriesResponse(name=name, series=series, request_id=request.state.request_id)


@router.get("/models/{model_id}", response_model=ModelDetailResponse)
def get_model(model_id: str, request: Request) -> ModelDetailResponse:
    registry = request.app.state.registry_service
    model, warnings = registry.get_model(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"model_id '{model_id}' not found")
    return ModelDetailResponse(
        model=model,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/models/{model_id}/metrics", response_model=ModelMetricsResponse)
def get_model_metrics(model_id: str, request: Request) -> ModelMetricsResponse:
    registry = request.app.state.registry_service
    metrics, warnings = registry.get_metrics(model_id)
    return ModelMetricsResponse(
        metrics=metrics,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/models/{model_id}/versions", response_model=ModelVersionsResponse)
def get_model_versions(model_id: str, request: Request) -> ModelVersionsResponse:
    registry = request.app.state.registry_service
    versions, warnings = registry.get_versions(model_id)
    return ModelVersionsResponse(
        versions=versions,
        warnings=warnings,
        request_id=request.state.request_id,
    )


@router.get("/models/{model_id}/explainability", response_model=ModelExplainabilityResponse)
def get_model_explainability(model_id: str, request: Request) -> ModelExplainabilityResponse:
    registry = request.app.state.registry_service
    explainability, warnings = registry.get_explainability(model_id)
    return ModelExplainabilityResponse(
        explainability=explainability,
        warnings=warnings,
        request_id=request.state.request_id,
    )
