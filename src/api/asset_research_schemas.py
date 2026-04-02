"""Schemas for grounded asset research endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .schemas import StrictModel


class AssetResearchAssetSchema(StrictModel):
    symbol: str
    asset_class: Literal["stock", "forex"]
    name: str


class GroundingDescriptorSchema(StrictModel):
    source: str
    status: Literal["used", "unavailable"]
    detail: str


class AssetResearchMemoSectionSchema(StrictModel):
    title: str
    content: str


class GenerateAssetMemoRequestSchema(StrictModel):
    asset_class: Literal["stock", "forex"]
    symbol: str = Field(min_length=1, max_length=64)


class GenerateAssetMemoResponseSchema(StrictModel):
    asset: AssetResearchAssetSchema
    generated_at: datetime
    sections: list[AssetResearchMemoSectionSchema]
    grounding: list[GroundingDescriptorSchema] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AskAssetResearchQuestionRequestSchema(StrictModel):
    asset_class: Literal["stock", "forex"]
    symbol: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=3, max_length=2000)


class AskAssetResearchQuestionResponseSchema(StrictModel):
    asset: AssetResearchAssetSchema
    question: str
    generated_at: datetime
    answer: str
    grounding: list[GroundingDescriptorSchema] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
