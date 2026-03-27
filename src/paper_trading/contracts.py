"""Domain contracts for the paper trading sandbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from market_data import Instrument


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaperOrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class PaperOrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class PaperOrderStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PaperSignalDirection(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class PaperAccountConfig:
    account_id: str = "paper-main"
    base_currency: str = "USD"
    initial_cash: float = 100_000.0
    allow_short: bool = False
    default_spread_bps: float = 0.0
    default_slippage_bps: float = 0.0
    commission_bps: float = 0.0
    commission_fixed: float = 0.0


@dataclass(frozen=True)
class PaperAccountState:
    account_id: str
    base_currency: str
    cash: float
    realized_pnl: float
    unrealized_pnl: float
    equity: float
    total_fees: float
    updated_at: datetime

    @staticmethod
    def from_config(config: PaperAccountConfig) -> "PaperAccountState":
        now = utcnow()
        return PaperAccountState(
            account_id=config.account_id,
            base_currency=config.base_currency,
            cash=config.initial_cash,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            equity=config.initial_cash,
            total_fees=0.0,
            updated_at=now,
        )


@dataclass(frozen=True)
class PaperPosition:
    instrument: Instrument
    quantity: float
    average_price: float
    mark_price: float | None = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class PaperOrderRequest:
    instrument: Instrument
    side: PaperOrderSide
    order_type: PaperOrderType
    quantity: float
    limit_price: float | None = None
    reference_price: float | None = None
    client_order_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaperOrder:
    order_id: str
    instrument: Instrument
    side: PaperOrderSide
    order_type: PaperOrderType
    quantity: float
    status: PaperOrderStatus
    created_at: datetime
    updated_at: datetime
    limit_price: float | None = None
    reference_price: float | None = None
    client_order_id: str | None = None
    rejection_reason: str | None = None
    filled_quantity: float = 0.0
    average_fill_price: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaperFill:
    fill_id: str
    order_id: str
    instrument: Instrument
    side: PaperOrderSide
    quantity: float
    fill_price: float
    notional: float
    commission: float
    spread_cost: float
    slippage_cost: float
    realized_pnl_delta: float
    timestamp: datetime


@dataclass(frozen=True)
class PriceUpdate:
    instrument: Instrument
    price: float
    timestamp: datetime = field(default_factory=utcnow)
    source: str = "manual"


@dataclass(frozen=True)
class PaperSignalIntent:
    instrument: Instrument
    direction: PaperSignalDirection
    quantity: float
    reference_price: float | None = None
    client_order_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaperStateSnapshot:
    config: PaperAccountConfig
    account: PaperAccountState
    positions: tuple[PaperPosition, ...]
    open_orders: tuple[PaperOrder, ...]
    fills: tuple[PaperFill, ...]
    price_book: Mapping[str, float]
    updated_at: datetime


@dataclass(frozen=True)
class PaperTradingState:
    config: PaperAccountConfig
    account: PaperAccountState
    positions: tuple[PaperPosition, ...] = ()
    orders: tuple[PaperOrder, ...] = ()
    fills: tuple[PaperFill, ...] = ()
    price_book: Mapping[str, float] = field(default_factory=dict)
    next_order_sequence: int = 1
    next_fill_sequence: int = 1
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class PaperOrderActionResult:
    order: PaperOrder
    fills: tuple[PaperFill, ...]
    state: PaperStateSnapshot


@dataclass(frozen=True)
class PaperCancelActionResult:
    order: PaperOrder
    state: PaperStateSnapshot


@dataclass(frozen=True)
class PaperPriceUpdateResult:
    filled_order_ids: tuple[str, ...]
    state: PaperStateSnapshot

