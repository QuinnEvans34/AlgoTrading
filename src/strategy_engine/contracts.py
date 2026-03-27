"""Domain contracts for the strategy subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from market_data.contracts import BarInterval, Candle, Instrument


class SignalDirection(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class StrategyInput:
    instrument: Instrument
    interval: BarInterval
    candles: tuple[Candle, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategySignal:
    strategy_name: str
    instrument: Instrument
    interval: BarInterval
    timestamp: datetime
    direction: SignalDirection
    confidence: float
    score: float
    rationale: tuple[str, ...]
    indicators: Mapping[str, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyEvaluation:
    strategy_name: str
    instrument: Instrument
    interval: BarInterval
    candle_count: int
    signal: StrategySignal | None
    indicators: Mapping[str, float] = field(default_factory=dict)
    diagnostics: Mapping[str, Any] = field(default_factory=dict)
