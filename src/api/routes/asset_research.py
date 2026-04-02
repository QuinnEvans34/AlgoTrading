"""Grounded asset research endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ..asset_research_schemas import (
    AskAssetResearchQuestionRequestSchema,
    AskAssetResearchQuestionResponseSchema,
    GenerateAssetMemoRequestSchema,
    GenerateAssetMemoResponseSchema,
)
from ..dependencies import get_api_service
from ..services import APIService

router = APIRouter(prefix="/asset-research", tags=["asset-research"])


@router.post("/memos", response_model=GenerateAssetMemoResponseSchema)
async def generate_asset_research_memo(
    request: GenerateAssetMemoRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> GenerateAssetMemoResponseSchema:
    return await run_in_threadpool(api_service.generate_asset_research_memo, request)


@router.post("/questions", response_model=AskAssetResearchQuestionResponseSchema)
async def ask_asset_research_question(
    request: AskAssetResearchQuestionRequestSchema,
    api_service: APIService = Depends(get_api_service),
) -> AskAssetResearchQuestionResponseSchema:
    return await run_in_threadpool(api_service.answer_asset_research_question, request)
