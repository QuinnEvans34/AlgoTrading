"""Pydantic schemas for live-execution boundary endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from market_data import AssetClass
from pydantic import BaseModel, ConfigDict, Field

from .schemas import InstrumentSchema


class StrictLiveModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LiveExecutionCapabilitiesSchema(StrictLiveModel):
    supported_asset_classes: list[AssetClass]
    supported_order_types: list[Literal["market", "limit"]]
    supported_order_sides: list[Literal["buy", "sell"]]
    supports_short: bool
    supports_cancel: bool
    supports_submit: bool


class LiveExecutionStatusResponseSchema(StrictLiveModel):
    broker_name: Literal["null", "oanda_stub"]
    configured: bool
    enabled: bool
    submission_allowed: bool
    state: Literal["disabled", "not_configured", "ready", "error"]
    message: str
    capabilities: LiveExecutionCapabilitiesSchema


class GuardCheckSchema(StrictLiveModel):
    name: str
    passed: bool
    code: str | None = None
    message: str


class LiveExecutionReadinessResponseSchema(StrictLiveModel):
    generated_at: datetime
    broker_name: Literal["null", "oanda_stub"]
    enabled: bool
    submission_allowed: bool
    configured: bool
    state: Literal["disabled", "not_configured", "ready", "error"]
    message: str
    manual_submission_ready: bool
    confirmation_phrase: str
    checks: list[GuardCheckSchema]


class LiveTradeIntentSchema(StrictLiveModel):
    instrument: InstrumentSchema
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: float = Field(gt=0)
    limit_price: float | None = Field(default=None, gt=0)
    client_order_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ManualLiveOrderRequestSchema(StrictLiveModel):
    intent: LiveTradeIntentSchema
    idempotency_key: str = Field(min_length=1)
    confirm_live_execution: bool
    confirmation_text: str
    operator_id: str | None = None
    operator_note: str | None = None


class LiveIntentValidationResponseSchema(StrictLiveModel):
    accepted: bool
    reasons: list[str]
    normalized_intent: LiveTradeIntentSchema | None = None
    broker_payload_preview: dict[str, Any] | None = None


class LiveSubmitResponseSchema(StrictLiveModel):
    accepted: bool
    status: str
    reason: str | None = None
    external_order_id: str | None = None
    broker_payload: dict[str, Any] | None = None


class ManualLiveSubmitResponseSchema(StrictLiveModel):
    accepted: bool
    status: str
    attempt_id: str
    broker_name: Literal["null", "oanda_stub"]
    rejection_code: str | None = None
    rejection_message: str | None = None
    external_order_id: str | None = None
    broker_payload: dict[str, Any] | None = None
    guard_checks: list[GuardCheckSchema]


class LiveExecutionAttemptRecordSchema(StrictLiveModel):
    attempt_id: str
    timestamp: datetime
    broker_name: Literal["null", "oanda_stub"]
    idempotency_key: str
    request_summary: dict[str, Any]
    guard_checks: list[GuardCheckSchema]
    accepted: bool
    status: str
    rejection_code: str | None = None
    rejection_message: str | None = None
    external_order_id: str | None = None


class LiveExecutionAttemptsResponseSchema(StrictLiveModel):
    attempts: list[LiveExecutionAttemptRecordSchema]
