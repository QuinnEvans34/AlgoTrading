"""Schemas for workflow persistence resources."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import Field

from .schemas import (
    InstrumentSchema,
    MLWorkflowSpecSchema,
    StrategyWorkflowSpecSchema,
    StrictModel,
)


class SavedConfigRunDefaultsSchema(StrictModel):
    run_name: str | None = None
    random_seed: int = 42
    strict_failures: bool = True
    persist_summary: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class InlineSampleCandleSourceSchema(StrictModel):
    source_type: Literal["inline_sample"] = "inline_sample"
    inline_bars: int = Field(ge=120, le=5000)


class SavedConfigMarketDataFetchSourceSchema(StrictModel):
    source_type: Literal["market_data_fetch"] = "market_data_fetch"
    provider_name: str
    start: datetime
    end: datetime
    limit: int | None = Field(default=None, gt=0)


SavedConfigCandleSourceSchema = Annotated[
    InlineSampleCandleSourceSchema | SavedConfigMarketDataFetchSourceSchema,
    Field(discriminator="source_type"),
]


class SavedStrategyConfigPayloadSchema(StrictModel):
    instrument: InstrumentSchema
    interval: str
    candle_source: SavedConfigCandleSourceSchema
    strategy_spec: StrategyWorkflowSpecSchema = Field(default_factory=StrategyWorkflowSpecSchema)
    run_config: SavedConfigRunDefaultsSchema = Field(default_factory=SavedConfigRunDefaultsSchema)


class SavedMLConfigPayloadSchema(StrictModel):
    instrument: InstrumentSchema
    interval: str
    candle_source: SavedConfigCandleSourceSchema
    ml_spec: MLWorkflowSpecSchema = Field(default_factory=MLWorkflowSpecSchema)
    run_config: SavedConfigRunDefaultsSchema = Field(default_factory=SavedConfigRunDefaultsSchema)


class SavedStrategyConfigWriteSchema(StrictModel):
    config_type: Literal["strategy"] = "strategy"
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    config_schema_version: int = 1
    payload: SavedStrategyConfigPayloadSchema


class SavedMLConfigWriteSchema(StrictModel):
    config_type: Literal["ml"] = "ml"
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    config_schema_version: int = 1
    payload: SavedMLConfigPayloadSchema


SavedResearchConfigWriteSchema = Annotated[
    SavedStrategyConfigWriteSchema | SavedMLConfigWriteSchema,
    Field(discriminator="config_type"),
]


class SavedResearchConfigSummarySchema(StrictModel):
    id: str
    config_type: str
    name: str
    description: str | None = None
    config_schema_version: int
    instrument_symbol: str
    asset_class: str
    interval: str
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None


class SavedResearchConfigResponseSchema(SavedResearchConfigSummarySchema):
    payload: dict[str, Any]


class SavedResearchConfigListResponseSchema(StrictModel):
    items: list[SavedResearchConfigSummarySchema]


class DeleteWorkflowObjectResponseSchema(StrictModel):
    deleted: bool


class WatchlistItemWriteSchema(StrictModel):
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: str = Field(min_length=1, max_length=64)
    source_context: str | None = Field(default=None, max_length=128)


class WatchlistItemResponseSchema(StrictModel):
    id: str
    symbol: str
    asset_class: str
    source_context: str | None = None
    created_at: datetime
    updated_at: datetime


class WatchlistResponseSchema(StrictModel):
    items: list[WatchlistItemResponseSchema]


class RecentAssetTouchSchema(StrictModel):
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: str = Field(min_length=1, max_length=64)
    source_context: str | None = Field(default=None, max_length=128)


class RecentAssetResponseSchema(StrictModel):
    id: str
    symbol: str
    asset_class: str
    source_context: str | None = None
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime


class RecentAssetListResponseSchema(StrictModel):
    items: list[RecentAssetResponseSchema]


class RecentCompareTouchSchema(StrictModel):
    compare_mode: Literal["auto", "strategy", "ml"] = "auto"
    run_ids: list[str] = Field(min_length=2, max_length=5)


class RecentCompareSetResponseSchema(StrictModel):
    id: str
    compare_mode: str
    run_ids: list[str]
    fingerprint: str
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime


class RecentCompareSetListResponseSchema(StrictModel):
    items: list[RecentCompareSetResponseSchema]
