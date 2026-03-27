"""Broker-agnostic contracts for the live-execution boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from market_data import AssetClass, Instrument


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LiveBrokerName(str, Enum):
    NULL = "null"
    OANDA_STUB = "oanda_stub"


class LiveOrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class LiveOrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class LiveConnectionState(str, Enum):
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    READY = "ready"
    ERROR = "error"


@dataclass(frozen=True)
class BrokerCapabilities:
    supported_asset_classes: tuple[AssetClass, ...]
    supported_order_types: tuple[LiveOrderType, ...]
    supported_order_sides: tuple[LiveOrderSide, ...]
    supports_short: bool
    supports_cancel: bool
    supports_submit: bool


@dataclass(frozen=True)
class LiveTradeIntent:
    instrument: Instrument
    side: LiveOrderSide
    order_type: LiveOrderType
    quantity: float
    limit_price: float | None = None
    client_order_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrokerConnectionStatus:
    broker_name: LiveBrokerName
    enabled: bool
    submission_allowed: bool
    configured: bool
    state: LiveConnectionState
    message: str
    capabilities: BrokerCapabilities


@dataclass(frozen=True)
class IntentValidationResult:
    accepted: bool
    reasons: tuple[str, ...]
    normalized_intent: LiveTradeIntent | None
    broker_payload_preview: Mapping[str, Any] | None


@dataclass(frozen=True)
class LiveSubmitResult:
    accepted: bool
    status: str
    reason: str | None = None
    external_order_id: str | None = None
    broker_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LiveBalanceSnapshot:
    currency: str
    cash: float
    equity: float
    buying_power: float | None = None
    timestamp: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class LivePositionSnapshot:
    instrument: Instrument
    quantity: float
    average_price: float | None = None
    mark_price: float | None = None
    unrealized_pnl: float | None = None
    realized_pnl: float | None = None


@dataclass(frozen=True)
class LiveOrderSnapshot:
    order_id: str
    instrument: Instrument
    side: LiveOrderSide
    order_type: LiveOrderType
    quantity: float
    status: str
    created_at: datetime
    updated_at: datetime
    limit_price: float | None = None
    client_order_id: str | None = None


@dataclass(frozen=True)
class LiveFillSnapshot:
    fill_id: str
    order_id: str
    instrument: Instrument
    side: LiveOrderSide
    quantity: float
    fill_price: float
    fee: float | None = None
    timestamp: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class LiveAccountSnapshot:
    account_id: str
    broker_name: LiveBrokerName
    balances: tuple[LiveBalanceSnapshot, ...] = ()
    positions: tuple[LivePositionSnapshot, ...] = ()
    open_orders: tuple[LiveOrderSnapshot, ...] = ()
    recent_fills: tuple[LiveFillSnapshot, ...] = ()
    timestamp: datetime = field(default_factory=utcnow)

