"""Market data preview endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..schemas import MarketDataPreviewRequestSchema, MarketDataPreviewResponseSchema
from ..services import APIService

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.post("/historical-preview", response_model=MarketDataPreviewResponseSchema)
async def historical_preview(
    request: MarketDataPreviewRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> MarketDataPreviewResponseSchema:
    return await run_in_threadpool(api_service.preview_historical_data, request)

