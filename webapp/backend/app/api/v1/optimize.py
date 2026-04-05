from __future__ import annotations

from fastapi import APIRouter, Request

from ...schemas.optimize import OptimizeSubmitRequest, OptimizeSubmitResponse
from ...services.inference.optimize_service import OptimizeService


router = APIRouter()


@router.post("/optimize/submit", response_model=OptimizeSubmitResponse)
def optimize_submit(payload: OptimizeSubmitRequest, request: Request) -> OptimizeSubmitResponse:
    service = OptimizeService(
        repo=request.app.state.data_repo,
        settings=request.app.state.settings,
        registry=request.app.state.registry_service,
    )

    constraints = payload.constraints.model_dump()
    candidate_promos = [p.model_dump() for p in payload.candidate_promos]
    products = payload.products

    job_manager = request.app.state.job_manager
    job = job_manager.create()

    def _run():
        result, _warnings = service.optimize(
            constraints=constraints,
            candidate_promos=candidate_promos,
            products=products,
        )
        return result

    job_manager.run(job, _run)

    return OptimizeSubmitResponse(
        job_id=job.job_id,
        status=job.status,
        request_id=request.state.request_id,
    )
