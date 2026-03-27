"""Paper trading sandbox endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..paper_trading_schemas import (
    PaperCancelActionResponseSchema,
    PaperOrderActionResponseSchema,
    PaperOrderRequestSchema,
    PaperPriceUpdateResponseSchema,
    PaperResetRequestSchema,
    PaperSignalIntentRequestSchema,
    PaperStateResponseSchema,
    PriceUpdateRequestSchema,
)
from ..services import APIService

router = APIRouter(prefix="/paper", tags=["paper-trading"])


@router.get("/state", response_model=PaperStateResponseSchema)
async def get_paper_state(
    fills_limit: int = Query(default=100, ge=1, le=5000),
    api_service: APIService = Depends(get_api_service),
) -> PaperStateResponseSchema:
    return await run_in_threadpool(api_service.get_paper_state, fills_limit=fills_limit)


@router.post("/orders", response_model=PaperOrderActionResponseSchema)
async def place_paper_order(
    request: PaperOrderRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> PaperOrderActionResponseSchema:
    return await run_in_threadpool(api_service.place_paper_order, request)


@router.post("/orders/{order_id}/cancel", response_model=PaperCancelActionResponseSchema)
async def cancel_paper_order(
    order_id: str,
    api_service: APIService = Depends(get_api_service),
) -> PaperCancelActionResponseSchema:
    return await run_in_threadpool(api_service.cancel_paper_order, order_id)


@router.post("/prices", response_model=PaperPriceUpdateResponseSchema)
async def process_paper_price(
    request: PriceUpdateRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> PaperPriceUpdateResponseSchema:
    return await run_in_threadpool(api_service.process_paper_price_update, request)


@router.post("/signals", response_model=PaperOrderActionResponseSchema)
async def submit_paper_signal(
    request: PaperSignalIntentRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> PaperOrderActionResponseSchema:
    return await run_in_threadpool(api_service.submit_paper_signal_intent, request)


@router.post("/reset", response_model=PaperStateResponseSchema)
async def reset_paper_account(
    request: PaperResetRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> PaperStateResponseSchema:
    return await run_in_threadpool(api_service.reset_paper_account, request)

