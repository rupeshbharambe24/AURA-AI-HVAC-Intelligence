from fastapi import APIRouter
from .anomaly import router as anomaly_router
from .forecast import router as forecast_router
from .health import router as health_router
from .models import router as models_router
from .optimize import router as optimize_router
from .market_share import router as market_share_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router, tags=["health"])
router.include_router(models_router, tags=["models"])
router.include_router(forecast_router, tags=["forecast"])
router.include_router(anomaly_router, tags=["anomaly"])
router.include_router(optimize_router, tags=["optimize"])
router.include_router(market_share_router, tags=["market-share"])
