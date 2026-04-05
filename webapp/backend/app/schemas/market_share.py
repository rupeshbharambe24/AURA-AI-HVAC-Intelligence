from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .common import BaseResponse


class MarketShareOptionsResponse(BaseResponse):
    products: List[str]
    supported_horizons_months: List[int]
    default_as_of_date: str


class MarketShareRequest(BaseModel):
    product_id: str
    horizon_months: int = Field(ge=3, le=6)
    as_of_date: Optional[str] = None
    news_filters: Optional[Dict[str, bool]] = None


class MarketShareForecastItem(BaseModel):
    month: str
    our_share: float
    lower: Optional[float] = None
    upper: Optional[float] = None


class MarketShareAlert(BaseModel):
    type: str
    message: str
    severity: str


class MarketShareNewsItem(BaseModel):
    date: str
    headline: str
    sentiment: str
    tags: List[str]
    relevance: float


class MarketShareDriver(BaseModel):
    name: str
    importance_pct: float


class MarketShareMetrics(BaseModel):
    mae_pct: Optional[float] = None
    rmse_pct: Optional[float] = None
    mape_pct: Optional[float] = None
    coverage_pct: Optional[float] = None


class MarketShareResponse(BaseResponse):
    product_id: str
    as_of_date: str
    horizon_months: int
    forecast: List[MarketShareForecastItem]
    alerts: List[MarketShareAlert]
    news_timeline: List[MarketShareNewsItem]
    drivers: List[MarketShareDriver]
    metrics: MarketShareMetrics
    warnings: List[str] = []


class MarketShareBatchResponse(BaseResponse):
    results: Optional[List[Dict[str, object]]] = None
    job_id: Optional[str] = None
    status: Optional[str] = None
    warnings: List[str] = []


class MarketShareMetricsResponse(BaseResponse):
    metrics: List[Dict[str, str]]
    warnings: List[str] = []
