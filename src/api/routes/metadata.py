"""Capability and metadata discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_api_service
from ..schemas import CapabilitiesResponseSchema
from ..services import APIService

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/capabilities", response_model=CapabilitiesResponseSchema)
async def capabilities(
    api_service: APIService = Depends(get_api_service),
) -> CapabilitiesResponseSchema:
    return api_service.capabilities()

