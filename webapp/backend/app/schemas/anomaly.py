from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .common import BaseResponse


class Evidence(BaseModel):
    type: str
    strength: float
    detail: str
    ref: Optional[str] = None


class AnomalyThresholds(BaseModel):
    point: float
    pattern: float
    trend: float


class AnomalyDetectRequest(BaseModel):
    product_id: str
    aps: str
    date_range: Optional[List[str]] = None
    thresholds: Optional[AnomalyThresholds] = None
    threshold: Optional[float] = None
    include_explanations: bool = True


class AnomalySeriesItem(BaseModel):
    date: str
    demand: float
    expected: float
    residual: float
    anomaly_score: float
    is_anomaly: bool
    anomaly_family: Optional[str] = None
    anomaly_type: Optional[str] = None
    root_cause: Optional[str] = None
    explanation: Optional[str] = None
    evidence: List[Evidence] = []


class AnomalySummary(BaseModel):
    total: int
    anomalies: int
    by_family: Dict[str, int]


class AnomalyDetectResponse(BaseResponse):
    product_id: str
    aps: str
    baseline_method: str
    effective_thresholds: AnomalyThresholds
    series: List[AnomalySeriesItem]
    summary: AnomalySummary
    warnings: List[str] = []


class AnomalyOptionsResponse(BaseResponse):
    products: List[str]
    aps_list: List[str]
    default_thresholds: AnomalyThresholds


class AnomalyMetricsResponse(BaseResponse):
    metrics: List[Dict[str, str]]
    warnings: List[str] = []


class AnomalyBatchResponse(BaseResponse):
    results: Optional[List[Dict[str, object]]] = None
    job_id: Optional[str] = None
    status: Optional[str] = None
    warnings: List[str] = []
