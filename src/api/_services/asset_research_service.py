"""API orchestration for grounded asset research memo generation and Q&A."""

from __future__ import annotations

from asset_research import (
    AssetResearchProviderError,
    AssetResearchService,
    AssetResearchUnavailableError,
)

from ..asset_research_schemas import (
    AskAssetResearchQuestionRequestSchema,
    AskAssetResearchQuestionResponseSchema,
    GenerateAssetMemoRequestSchema,
    GenerateAssetMemoResponseSchema,
)
from ..errors import APIError


class AssetResearchAPIService:
    def __init__(self, *, asset_research_service: AssetResearchService) -> None:
        self._asset_research_service = asset_research_service

    @staticmethod
    def _asset_payload(result) -> dict[str, str]:  # noqa: ANN001
        return {
            "symbol": result.symbol,
            "asset_class": result.asset_class,
            "name": result.name,
        }

    def generate_memo(
        self,
        request: GenerateAssetMemoRequestSchema,
    ) -> GenerateAssetMemoResponseSchema:
        try:
            result = self._asset_research_service.generate_memo(
                asset_class=request.asset_class,
                symbol=request.symbol.strip().upper(),
            )
        except AssetResearchUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="asset_research_unavailable",
                message=str(exc),
            ) from exc
        except AssetResearchProviderError as exc:
            raise APIError(
                status_code=502,
                code="asset_research_provider_error",
                message=str(exc),
            ) from exc
        return GenerateAssetMemoResponseSchema.model_validate(
            {
                "asset": self._asset_payload(result),
                "generated_at": result.generated_at,
                "sections": [
                    {"title": section.title, "content": section.content}
                    for section in result.sections
                ],
                "grounding": [
                    {
                        "source": item.source,
                        "status": item.status,
                        "detail": item.detail,
                    }
                    for item in result.grounding
                ],
                "warnings": list(result.warnings),
            }
        )

    def answer_question(
        self,
        request: AskAssetResearchQuestionRequestSchema,
    ) -> AskAssetResearchQuestionResponseSchema:
        try:
            result = self._asset_research_service.answer_question(
                asset_class=request.asset_class,
                symbol=request.symbol.strip().upper(),
                question=request.question.strip(),
            )
        except AssetResearchUnavailableError as exc:
            raise APIError(
                status_code=503,
                code="asset_research_unavailable",
                message=str(exc),
            ) from exc
        except AssetResearchProviderError as exc:
            raise APIError(
                status_code=502,
                code="asset_research_provider_error",
                message=str(exc),
            ) from exc
        return AskAssetResearchQuestionResponseSchema.model_validate(
            {
                "asset": self._asset_payload(result),
                "question": result.question,
                "generated_at": result.generated_at,
                "answer": result.answer,
                "grounding": [
                    {
                        "source": item.source,
                        "status": item.status,
                        "detail": item.detail,
                    }
                    for item in result.grounding
                ],
                "warnings": list(result.warnings),
            }
        )
