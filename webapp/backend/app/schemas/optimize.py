from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import BaseResponse


class OptimizeConstraints(BaseModel):
    max_promos_per_year: int = Field(ge=0, default=3)
    exclude_months: List[int] = []
    capacity_limit_pct: Optional[float] = None
    variance_limit_ratio: Optional[float] = None
    chance_level: Optional[float] = None
    min_mean_uplift_pct: Optional[float] = None
    target_year: Optional[int] = None


class PromoTemplate(BaseModel):
    type: str = "discount"
    discount_pct: float = 0.0
    duration_weeks: int = Field(ge=1, default=3)


class OptimizeSubmitRequest(BaseModel):
    constraints: OptimizeConstraints
    candidate_promos: List[PromoTemplate]
    products: List[str] = []


class OptimizeSubmitResponse(BaseResponse):
    job_id: str
    status: str
