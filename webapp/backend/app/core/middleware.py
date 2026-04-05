from __future__ import annotations

import json
import time
import uuid
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response


async def request_context_middleware(request: Request, call_next: Callable) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start = time.perf_counter()
    logger = getattr(request.app.state, "logger", None)

    if logger:
        logger.info(
            "request_start",
            extra={"request_id": request_id, "path": request.url.path},
        )

    try:
        response = await call_next(request)
    except Exception:
        if logger:
            logger.exception(
                "request_error",
                extra={"request_id": request_id, "path": request.url.path},
            )
        raise

    latency_ms = (time.perf_counter() - start) * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = f"{latency_ms:.2f}"

    response = _ensure_request_id_in_json(response, request_id)

    if logger:
        logger.info(
            "request_end",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
            },
        )

    # Update metrics
    metrics = getattr(request.app.state, "metrics", None)
    if isinstance(metrics, dict):
        metrics["count"] = metrics.get("count", 0) + 1
        metrics["latency_sum"] = metrics.get("latency_sum", 0.0) + latency_ms
        if response.status_code >= 400:
            metrics["error_count"] = metrics.get("error_count", 0) + 1

    return response


def _ensure_request_id_in_json(response: Response, request_id: str) -> Response:
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response

    body = getattr(response, "body", None)
    if body is None:
        return response

    try:
        payload = json.loads(body)
    except Exception:
        return response

    if isinstance(payload, dict):
        if "request_id" not in payload:
            payload["request_id"] = request_id
    else:
        payload = {"data": payload, "request_id": request_id}

    new_response = JSONResponse(
        content=payload,
        status_code=response.status_code,
    )
    for k, v in response.headers.items():
        new_response.headers[k] = v
    return new_response

