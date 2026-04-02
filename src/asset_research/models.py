"""Typed contracts for asset-research context and outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class CatalogAssetRecord:
    symbol: str
    asset_class: Literal["stock", "forex"]
    name: str
    headline: str
    description: str
    tags: tuple[str, ...]
    preferred_interval: str
    performance_lookback_days: int
    profile_bullets: tuple[str, ...]
    performance_focus: tuple[str, ...]
    ai_prompts: tuple[str, ...]
    sector: str | None = None
    exchange: str | None = None
    filings_focus: tuple[str, ...] = ()
    region: str | None = None
    macro_drivers: tuple[str, ...] = ()


@dataclass(frozen=True)
class SavedConfigNote:
    id: str
    config_type: str
    name: str
    interval: str
    updated_at: datetime


@dataclass(frozen=True)
class RelatedRunNote:
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    interval: str | None
    started_at: datetime | None
    has_strategy: bool
    has_ml: bool


@dataclass(frozen=True)
class MarketPriceSnapshot:
    provider: str
    interval: str
    candle_count: int
    period_start: datetime
    period_end: datetime
    latest_close: float
    net_change: float
    net_change_pct: float
    low: float
    high: float


@dataclass(frozen=True)
class GroundingDescriptor:
    source: str
    status: Literal["used", "unavailable"]
    detail: str


@dataclass(frozen=True)
class AssetResearchContext:
    asset: CatalogAssetRecord
    saved_configs: tuple[SavedConfigNote, ...]
    related_runs: tuple[RelatedRunNote, ...]
    market_price: MarketPriceSnapshot | None
    grounding: tuple[GroundingDescriptor, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class AssetResearchMemoSection:
    title: str
    content: str


@dataclass(frozen=True)
class AssetResearchMemoResult:
    asset_class: Literal["stock", "forex"]
    symbol: str
    name: str
    generated_at: datetime
    sections: tuple[AssetResearchMemoSection, ...]
    grounding: tuple[GroundingDescriptor, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class AssetResearchQuestionResult:
    asset_class: Literal["stock", "forex"]
    symbol: str
    name: str
    question: str
    generated_at: datetime
    answer: str
    grounding: tuple[GroundingDescriptor, ...]
    warnings: tuple[str, ...]


class StrictStructuredModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StructuredStockMemoPayload(StrictStructuredModel):
    overview: str = Field(min_length=1)
    recent_price_performance_context: str = Field(min_length=1)
    business_profile_context: str = Field(min_length=1)
    filing_fundamental_highlights: str = Field(min_length=1)
    risks_open_questions: str = Field(min_length=1)
    bottom_line_takeaway: str = Field(min_length=1)


class StructuredForexMemoPayload(StrictStructuredModel):
    overview: str = Field(min_length=1)
    recent_price_performance_context: str = Field(min_length=1)
    macro_context: str = Field(min_length=1)
    key_drivers: str = Field(min_length=1)
    risks_open_questions: str = Field(min_length=1)
    bottom_line_takeaway: str = Field(min_length=1)


class StructuredQuestionPayload(StrictStructuredModel):
    answer: str = Field(min_length=1)
