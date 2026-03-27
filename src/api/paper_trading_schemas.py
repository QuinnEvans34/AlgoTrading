"""Pydantic schemas for paper trading endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from market_data import AssetClass
from pydantic import BaseModel, ConfigDict, Field

from .schemas import InstrumentSchema


class StrictPaperModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaperAccountConfigSchema(StrictPaperModel):
    account_id: str
    base_currency: str
    initial_cash: float
    allow_short: bool
    default_spread_bps: float
    default_slippage_bps: float
    commission_bps: float
    commission_fixed: float


class PaperAccountStateSchema(StrictPaperModel):
    account_id: str
    base_currency: str
    cash: float
    realized_pnl: float
    unrealized_pnl: float
    equity: float
    total_fees: float
    updated_at: datetime


class PaperPositionSchema(StrictPaperModel):
    instrument: InstrumentSchema
    quantity: float
    average_price: float
    mark_price: float | None = None
    unrealized_pnl: float
    realized_pnl: float
    updated_at: datetime


class PaperOrderSchema(StrictPaperModel):
    order_id: str
    instrument: InstrumentSchema
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: float
    status: Literal["open", "filled", "cancelled", "rejected"]
    created_at: datetime
    updated_at: datetime
    limit_price: float | None = None
    reference_price: float | None = None
    client_order_id: str | None = None
    rejection_reason: str | None = None
    filled_quantity: float
    average_fill_price: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperFillSchema(StrictPaperModel):
    fill_id: str
    order_id: str
    instrument: InstrumentSchema
    side: Literal["buy", "sell"]
    quantity: float
    fill_price: float
    notional: float
    commission: float
    spread_cost: float
    slippage_cost: float
    realized_pnl_delta: float
    timestamp: datetime


class PaperStateResponseSchema(StrictPaperModel):
    config: PaperAccountConfigSchema
    account: PaperAccountStateSchema
    positions: list[PaperPositionSchema]
    open_orders: list[PaperOrderSchema]
    fills: list[PaperFillSchema]
    price_book: dict[str, float] = Field(default_factory=dict)
    updated_at: datetime


class PaperOrderRequestSchema(StrictPaperModel):
    instrument: InstrumentSchema
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: float = Field(gt=0)
    limit_price: float | None = Field(default=None, gt=0)
    reference_price: float | None = Field(default=None, gt=0)
    client_order_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperOrderActionResponseSchema(StrictPaperModel):
    order: PaperOrderSchema
    fills: list[PaperFillSchema]
    state: PaperStateResponseSchema


class PaperCancelActionResponseSchema(StrictPaperModel):
    order: PaperOrderSchema
    state: PaperStateResponseSchema


class PriceUpdateRequestSchema(StrictPaperModel):
    instrument: InstrumentSchema
    price: float = Field(gt=0)
    timestamp: datetime | None = None
    source: str = "manual"


class PaperPriceUpdateResponseSchema(StrictPaperModel):
    filled_order_ids: list[str]
    state: PaperStateResponseSchema


class PaperSignalIntentRequestSchema(StrictPaperModel):
    instrument: InstrumentSchema
    direction: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    reference_price: float | None = Field(default=None, gt=0)
    client_order_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaperResetRequestSchema(StrictPaperModel):
    account_id: str | None = None
    base_currency: str | None = None
    initial_cash: float | None = Field(default=None, gt=0)
    allow_short: bool | None = None
    default_spread_bps: float | None = Field(default=None, ge=0)
    default_slippage_bps: float | None = Field(default=None, ge=0)
    commission_bps: float | None = Field(default=None, ge=0)
    commission_fixed: float | None = Field(default=None, ge=0)


class PaperTradingCapabilitiesSchema(StrictPaperModel):
    supported_order_types: list[str]
    supported_order_sides: list[str]
    supports_short: bool
    supports_signal_intents: bool
    supported_asset_classes: list[AssetClass]

