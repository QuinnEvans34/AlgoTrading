"""Research run trigger endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..schemas import (
    HybridRunRequestSchema,
    MLRunRequestSchema,
    RunSummaryResponseSchema,
    StrategyRunRequestSchema,
)
from ..services import APIService

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/strategy-runs", response_model=RunSummaryResponseSchema)
async def create_strategy_run(
    request: StrategyRunRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> RunSummaryResponseSchema:
    return await run_in_threadpool(api_service.run_strategy, request)


@router.post("/ml-runs", response_model=RunSummaryResponseSchema)
async def create_ml_run(
    request: MLRunRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> RunSummaryResponseSchema:
    return await run_in_threadpool(api_service.run_ml, request)


@router.post("/hybrid-runs", response_model=RunSummaryResponseSchema)
async def create_hybrid_run(
    request: HybridRunRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> RunSummaryResponseSchema:
    return await run_in_threadpool(api_service.run_hybrid, request)

