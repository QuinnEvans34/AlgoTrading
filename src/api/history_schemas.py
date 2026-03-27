"""Schemas dedicated to run-history and compare endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .schemas import RunDetailResponseSchema, RunSummaryResponseSchema


class StrictHistoryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RunHistoryItemSchema(StrictHistoryModel):
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    instrument_symbol: str
    asset_class: str | None = None
    interval: str | None = None
    has_strategy: bool
    has_ml: bool
    summary_available: bool
    detail_available: bool
    updated_at: datetime


class RunHistoryListResponseSchema(StrictHistoryModel):
    items: list[RunHistoryItemSchema]
    total: int
    limit: int
    offset: int
    warnings: list[str] = Field(default_factory=list)


class RunManifestResponseSchema(StrictHistoryModel):
    schema_version: int
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    instrument_symbol: str
    asset_class: str | None = None
    interval: str | None = None
    candle_count: int | None = None
    has_strategy: bool
    has_ml: bool
    summary_path: str
    detail_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    synthetic: bool = False


class HistoryReadResponseSchema(StrictHistoryModel):
    manifest: RunManifestResponseSchema
    summary: RunSummaryResponseSchema
    detail: RunDetailResponseSchema


class CompareRunsRequestSchema(StrictHistoryModel):
    run_ids: list[str] = Field(min_length=2, max_length=5)
    mode: Literal["auto", "strategy", "ml"] = "auto"

    @field_validator("run_ids")
    @classmethod
    def validate_run_ids(cls, value: list[str]) -> list[str]:
        clean = [item.strip() for item in value if item.strip()]
        if len(set(clean)) != len(clean):
            raise ValueError("run_ids must be unique")
        if len(clean) < 2 or len(clean) > 5:
            raise ValueError("compare requires between 2 and 5 unique run_ids")
        return clean


class CompareMetricCardSchema(StrictHistoryModel):
    label: str
    direction: str
    best_run_id: str | None = None
    best_value: float | None = None
    worst_run_id: str | None = None
    worst_value: float | None = None


class CompareRunsResponseSchema(StrictHistoryModel):
    mode: Literal["strategy", "ml"]
    warnings: list[str] = Field(default_factory=list)
    cards: list[CompareMetricCardSchema] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
