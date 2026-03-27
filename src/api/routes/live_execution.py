"""Safe live-execution boundary endpoints (status + validate + guarded submit)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..live_execution_schemas import (
    LiveExecutionAttemptsResponseSchema,
    LiveExecutionReadinessResponseSchema,
    LiveExecutionStatusResponseSchema,
    LiveIntentValidationResponseSchema,
    ManualLiveOrderRequestSchema,
    ManualLiveSubmitResponseSchema,
    LiveSubmitResponseSchema,
    LiveTradeIntentSchema,
)
from ..services import APIService

router = APIRouter(prefix="/live-execution", tags=["live-execution"])


@router.get("/status", response_model=LiveExecutionStatusResponseSchema)
async def live_execution_status(
    api_service: APIService = Depends(get_api_service),
) -> LiveExecutionStatusResponseSchema:
    return await run_in_threadpool(api_service.get_live_execution_status)


@router.get("/readiness", response_model=LiveExecutionReadinessResponseSchema)
async def live_execution_readiness(
    api_service: APIService = Depends(get_api_service),
) -> LiveExecutionReadinessResponseSchema:
    return await run_in_threadpool(api_service.get_live_execution_readiness)


@router.post("/intents/validate", response_model=LiveIntentValidationResponseSchema)
async def validate_intent(
    request: LiveTradeIntentSchema,
    api_service: APIService = Depends(get_api_service),
) -> LiveIntentValidationResponseSchema:
    return await run_in_threadpool(api_service.validate_live_intent, request)


@router.post("/intents/submit", response_model=LiveSubmitResponseSchema)
async def submit_intent(
    request: LiveTradeIntentSchema,
    api_service: APIService = Depends(get_api_service),
) -> LiveSubmitResponseSchema:
    return await run_in_threadpool(api_service.submit_live_intent, request)


@router.post("/manual-orders", response_model=ManualLiveSubmitResponseSchema)
async def submit_manual_order(
    request: ManualLiveOrderRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> ManualLiveSubmitResponseSchema:
    return await run_in_threadpool(api_service.submit_manual_live_order, request)


@router.get("/attempts", response_model=LiveExecutionAttemptsResponseSchema)
async def list_attempts(
    limit: int = Query(default=25, ge=1, le=200),
    api_service: APIService = Depends(get_api_service),
) -> LiveExecutionAttemptsResponseSchema:
    return await run_in_threadpool(api_service.list_live_execution_attempts, limit)
