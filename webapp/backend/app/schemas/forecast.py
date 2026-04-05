from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .common import BaseResponse


class ForecastOptionsResponse(BaseResponse):
    products: List[str]
    aps_list: List[str]
    max_horizon_months: int


class ForecastRequest(BaseModel):
    product_id: str
    aps: str
    horizon_months: int = Field(ge=1, le=12)
    cutoff_date: Optional[str] = None
    scenarios: Optional[Dict[str, float]] = None
    include_actuals: bool = True
    include_explain: bool = False


class ForecastItem(BaseModel):
    date: str
    actual: Optional[float] = None
    predicted: float
    lower: Optional[float] = None
    upper: Optional[float] = None
    drivers: List[str] = []


class ForecastMetrics(BaseModel):
    mape: Optional[float] = None
    rmse: Optional[float] = None
    coverage_95: Optional[float] = None
    bias_pct: Optional[float] = None


class ExplainItem(BaseModel):
    feature: str
    importance: float


class Explainability(BaseModel):
    local: List[ExplainItem] = []
    global_: List[ExplainItem] = Field(default_factory=list, alias="global")


class ForecastResponse(BaseResponse):
    model_id: str
    product_id: str
    aps: str
    cutoff_date: str
    forecast: List[ForecastItem]
    metrics: ForecastMetrics
    explain: Optional[Explainability] = None
    applied_scenarios: Dict[str, Dict[str, float]] = {}
    warnings: List[str] = []


class ForecastModelMetricsResponse(BaseResponse):
    metrics: List[Dict[str, str]]
    warnings: List[str] = []
