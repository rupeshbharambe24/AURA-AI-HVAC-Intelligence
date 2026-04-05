from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from .common import BaseResponse


class ModelRegistryEntry(BaseModel):
    id: str
    name: str
    version: str
    alias: str
    owner: Optional[str] = None
    status: str
    training_period: Optional[str] = None
    dataset_hash: Optional[str] = None
    key_metric: Optional[str] = None
    bundle_filename: Optional[str] = None
    notes: Optional[str] = None


class MetricEntry(BaseModel):
    label: str
    value: str


class VersionEntry(BaseModel):
    version: str
    date: Optional[str] = None
    run_id: Optional[str] = None
    note: Optional[str] = None


class ExplainabilityEntry(BaseModel):
    feature: str
    importance: float


class ModelListResponse(BaseResponse):
    models: List[ModelRegistryEntry]
    warnings: List[str] = []


class ModelDetailResponse(BaseResponse):
    model: ModelRegistryEntry
    warnings: List[str] = []


class ModelMetricsResponse(BaseResponse):
    metrics: List[MetricEntry]
    warnings: List[str] = []


class ModelVersionsResponse(BaseResponse):
    versions: List[VersionEntry]
    warnings: List[str] = []


class ModelExplainabilityResponse(BaseResponse):
    explainability: List[ExplainabilityEntry]
    warnings: List[str] = []


class DatasetEntry(BaseModel):
    name: str
    rows: int
    cols: int
    lastUpdated: Optional[str] = None
    quality: Optional[float] = None
    missingness: Optional[float] = None


class DatasetsResponse(BaseResponse):
    datasets: List[DatasetEntry]
    warnings: List[str] = []


class DatasetRowsResponse(BaseResponse):
    name: str
    rows: List[dict]


class DatasetTimeseriesResponse(BaseResponse):
    name: str
    series: List[dict]
