"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_api_service
from ..schemas import HealthResponseSchema
from ..services import APIService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponseSchema)
async def health(api_service: APIService = Depends(get_api_service)) -> HealthResponseSchema:
    return api_service.health()

