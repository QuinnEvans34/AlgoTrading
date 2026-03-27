"""Run summary retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..schemas import (
    RunDetailResponseSchema,
    RunSummaryResponseSchema,
    StoredRunSummaryListResponseSchema,
)
from ..services import APIService

router = APIRouter(prefix="/research", tags=["results"])


@router.get("/runs", response_model=StoredRunSummaryListResponseSchema)
async def list_run_summaries(
    limit: int = Query(default=50, ge=1, le=500),
    api_service: APIService = Depends(get_api_service),
) -> StoredRunSummaryListResponseSchema:
    return await run_in_threadpool(api_service.list_saved_run_summaries, limit=limit)


@router.get("/runs/{run_id}/summary", response_model=RunSummaryResponseSchema)
async def get_run_summary(
    run_id: str,
    api_service: APIService = Depends(get_api_service),
) -> RunSummaryResponseSchema:
    return await run_in_threadpool(api_service.get_saved_run_summary, run_id)


@router.get("/runs/{run_id}/detail", response_model=RunDetailResponseSchema)
async def get_run_detail(
    run_id: str,
    api_service: APIService = Depends(get_api_service),
) -> RunDetailResponseSchema:
    return await run_in_threadpool(api_service.get_saved_run_detail, run_id)
