from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1.router import router as v1_router
from .core.config import get_settings
from .core.logging import init_logging
from .core.middleware import request_context_middleware
from .schemas.common import ErrorResponse
from .services.bundles.loader import ModelRegistryService
from .services.data.repository import DataRepository
from .services.jobs.manager import JobManager


def create_app() -> FastAPI:
    settings = get_settings()
    logger = init_logging(settings.ENV)

    app = FastAPI(
        title="Scale AI Backend",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.state.settings = settings
    app.state.logger = logger
    app.state.metrics = {"count": 0, "error_count": 0, "latency_sum": 0.0}

    backend_dir = Path(__file__).resolve().parents[1]
    registry_path = backend_dir / "models" / "model_registry.json"
    app.state.registry_service = ModelRegistryService(
        registry_path=registry_path,
        model_dir=settings.MODEL_DIR,
    )
    app.state.data_repo = DataRepository(settings.DATA_DIR)
    app.state.job_manager = JobManager()

    app.middleware("http")(request_context_middleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)

    @app.on_event("startup")
    def _startup() -> None:
        logger.info(
            "startup_config",
            extra={
                "env": settings.ENV,
                "host": settings.HOST,
                "port": settings.PORT,
                "model_dir": str(settings.MODEL_DIR),
                "data_dir": str(settings.DATA_DIR),
            },
        )

        if settings.ENV.lower() == "prod":
            if not settings.MODEL_DIR.exists():
                raise RuntimeError(f"MODEL_DIR missing: {settings.MODEL_DIR}")
            if not settings.DATA_DIR.exists():
                raise RuntimeError(f"DATA_DIR missing: {settings.DATA_DIR}")
        else:
            if not settings.MODEL_DIR.exists():
                logger.warning("MODEL_DIR missing", extra={"model_dir": str(settings.MODEL_DIR)})
            if not settings.DATA_DIR.exists():
                logger.warning("DATA_DIR missing", extra={"data_dir": str(settings.DATA_DIR)})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", "unknown")
        payload = ErrorResponse(
            error="validation_error" if 400 <= exc.status_code < 500 else "server_error",
            message=str(exc.detail),
            request_id=request_id,
            details=None,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        payload = ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            request_id=request_id,
            details=exc.errors(),
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception("unhandled_error", extra={"request_id": request_id})
        payload = ErrorResponse(
            error="server_error",
            message="Unexpected server error",
            request_id=request_id,
            details=None,
        )
        return JSONResponse(status_code=500, content=payload.model_dump())

    return app


app = create_app()
