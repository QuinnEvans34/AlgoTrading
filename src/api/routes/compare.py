"""Compare-runs endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..history_schemas import CompareRunsRequestSchema, CompareRunsResponseSchema
from ..services import APIService

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("/runs", response_model=CompareRunsResponseSchema)
async def compare_runs(
    request: CompareRunsRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> CompareRunsResponseSchema:
    return await run_in_threadpool(api_service.compare_runs, request)
