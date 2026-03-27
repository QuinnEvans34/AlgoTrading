"""Safe runtime settings/status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ..dependencies import get_api_service
from ..services import APIService
from ..settings_schemas import SystemSettingsResponseSchema

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/system", response_model=SystemSettingsResponseSchema)
async def get_system_settings(
    api_service: APIService = Depends(get_api_service),
) -> SystemSettingsResponseSchema:
    return await run_in_threadpool(api_service.get_system_settings)

