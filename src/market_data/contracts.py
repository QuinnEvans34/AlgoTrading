"""Typed contracts for provider-agnostic market data access."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class AssetClass(str, Enum):
    STOCK = "stock"
    FOREX = "forex"


class BarInterval(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


def ensure_utc(dt: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class Instrument:
    """Provider-neutral instrument identity."""

    symbol: str
    asset_class: AssetClass
    venue: str | None = None
    quote_currency: str | None = None


@dataclass(frozen=True)
class HistoricalCandleRequest:
    instrument: Instrument
    interval: BarInterval
    start: datetime
    end: datetime
    limit: int | None = None

    def validated_range(self) -> tuple[datetime, datetime]:
        start = ensure_utc(self.start)
        end = ensure_utc(self.end)
        if start >= end:
            raise ValueError("HistoricalCandleRequest.start must be before end")
        return start, end


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True)
class HistoricalCandleResponse:
    provider: str
    instrument: Instrument
    interval: BarInterval
    candles: tuple[Candle, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LiveQuoteRequest:
    instrument: Instrument


@dataclass(frozen=True)
class Quote:
    provider: str
    instrument: Instrument
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
    mid: float | None = None
    last: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
