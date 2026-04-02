"""Workflow persistence endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..services import APIService
from ..workflow_schemas import (
    DeleteWorkflowObjectResponseSchema,
    RecentAssetListResponseSchema,
    RecentAssetResponseSchema,
    RecentAssetTouchSchema,
    RecentCompareSetListResponseSchema,
    RecentCompareSetResponseSchema,
    RecentCompareTouchSchema,
    SavedResearchConfigListResponseSchema,
    SavedResearchConfigResponseSchema,
    SavedResearchConfigWriteSchema,
    WatchlistItemResponseSchema,
    WatchlistItemWriteSchema,
    WatchlistResponseSchema,
)

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/saved-configs", response_model=SavedResearchConfigListResponseSchema)
async def list_saved_configs(
    config_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    api_service: APIService = Depends(get_api_service),
) -> SavedResearchConfigListResponseSchema:
    return await run_in_threadpool(
        api_service.list_saved_configs,
        config_type=config_type,
        limit=limit,
    )


@router.post("/saved-configs", response_model=SavedResearchConfigResponseSchema)
async def create_saved_config(
    request: SavedResearchConfigWriteSchema,
    api_service: APIService = Depends(get_api_service),
) -> SavedResearchConfigResponseSchema:
    return await run_in_threadpool(api_service.create_saved_config, request)


@router.get("/saved-configs/{config_id}", response_model=SavedResearchConfigResponseSchema)
async def get_saved_config(
    config_id: str,
    api_service: APIService = Depends(get_api_service),
) -> SavedResearchConfigResponseSchema:
    return await run_in_threadpool(api_service.get_saved_config, config_id)


@router.put("/saved-configs/{config_id}", response_model=SavedResearchConfigResponseSchema)
async def update_saved_config(
    config_id: str,
    request: SavedResearchConfigWriteSchema,
    api_service: APIService = Depends(get_api_service),
) -> SavedResearchConfigResponseSchema:
    return await run_in_threadpool(api_service.update_saved_config, config_id, request)


@router.delete(
    "/saved-configs/{config_id}",
    response_model=DeleteWorkflowObjectResponseSchema,
)
async def delete_saved_config(
    config_id: str,
    api_service: APIService = Depends(get_api_service),
) -> DeleteWorkflowObjectResponseSchema:
    return await run_in_threadpool(api_service.delete_saved_config, config_id)


@router.get("/watchlist", response_model=WatchlistResponseSchema)
async def list_watchlist(
    limit: int = Query(default=100, ge=1, le=500),
    api_service: APIService = Depends(get_api_service),
) -> WatchlistResponseSchema:
    return await run_in_threadpool(api_service.list_watchlist, limit=limit)


@router.post("/watchlist/items", response_model=WatchlistItemResponseSchema)
async def add_watchlist_item(
    request: WatchlistItemWriteSchema,
    api_service: APIService = Depends(get_api_service),
) -> WatchlistItemResponseSchema:
    return await run_in_threadpool(api_service.add_watchlist_item, request)


@router.delete(
    "/watchlist/items/{asset_class}/{symbol}",
    response_model=DeleteWorkflowObjectResponseSchema,
)
async def delete_watchlist_item(
    asset_class: str = Path(...),
    symbol: str = Path(...),
    api_service: APIService = Depends(get_api_service),
) -> DeleteWorkflowObjectResponseSchema:
    return await run_in_threadpool(
        api_service.delete_watchlist_item,
        asset_class=asset_class,
        symbol=symbol,
    )


@router.get("/recent-assets", response_model=RecentAssetListResponseSchema)
async def list_recent_assets(
    limit: int = Query(default=20, ge=1, le=200),
    api_service: APIService = Depends(get_api_service),
) -> RecentAssetListResponseSchema:
    return await run_in_threadpool(api_service.list_recent_assets, limit=limit)


@router.post("/recent-assets/touch", response_model=RecentAssetResponseSchema)
async def touch_recent_asset(
    request: RecentAssetTouchSchema,
    api_service: APIService = Depends(get_api_service),
) -> RecentAssetResponseSchema:
    return await run_in_threadpool(api_service.touch_recent_asset, request)


@router.get("/recent-compares", response_model=RecentCompareSetListResponseSchema)
async def list_recent_compares(
    limit: int = Query(default=20, ge=1, le=200),
    api_service: APIService = Depends(get_api_service),
) -> RecentCompareSetListResponseSchema:
    return await run_in_threadpool(api_service.list_recent_compares, limit=limit)


@router.post("/recent-compares/touch", response_model=RecentCompareSetResponseSchema)
async def touch_recent_compare(
    request: RecentCompareTouchSchema,
    api_service: APIService = Depends(get_api_service),
) -> RecentCompareSetResponseSchema:
    return await run_in_threadpool(api_service.touch_recent_compare, request)
