"""Domain contracts for research backtesting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from market_data.contracts import BarInterval, Candle, Instrument
from strategy_engine.contracts import SignalDirection


class PositionDirection(str, Enum):
    LONG = "long"
    SHORT = "short"


class ExecutionTiming(str, Enum):
    NEXT_BAR_OPEN = "next_bar_open"


class SizingMode(str, Enum):
    FIXED_EQUITY_FRACTION = "fixed_equity_fraction"


class IntrabarExitPolicy(str, Enum):
    ADVERSE_FIRST = "adverse_first"


class ExitReason(str, Enum):
    SIGNAL_FLIP = "signal_flip"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    MAX_BARS_TIMEOUT = "max_bars_timeout"
    END_OF_DATA = "end_of_data"


@dataclass(frozen=True)
class BacktestInput:
    instrument: Instrument
    interval: BarInterval
    candles: tuple[Candle, ...]


@dataclass(frozen=True)
class RiskExitConfig:
    stop_loss_fraction: float | None = None
    take_profit_fraction: float | None = None
    intrabar_exit_policy: IntrabarExitPolicy = IntrabarExitPolicy.ADVERSE_FIRST


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float = 100_000.0
    warmup_bars: int = 80
    allow_short: bool = True
    allow_flip: bool = True
    close_position_on_end: bool = True
    max_bars_in_position: int | None = None
    min_signal_confidence: float = 0.0
    sizing_mode: SizingMode = SizingMode.FIXED_EQUITY_FRACTION
    position_notional_fraction: float = 1.0
    entry_timing: ExecutionTiming = ExecutionTiming.NEXT_BAR_OPEN
    signal_exit_timing: ExecutionTiming = ExecutionTiming.NEXT_BAR_OPEN
    risk_exits: RiskExitConfig | None = None


@dataclass(frozen=True)
class SignalEvent:
    timestamp: datetime
    direction: SignalDirection
    confidence: float
    score: float
    rationale: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Position:
    direction: PositionDirection
    entry_time: datetime
    entry_price: float
    units: float
    entry_equity: float
    entry_commission: float = 0.0
    entry_signal: SignalEvent | None = None
    stop_loss_price: float | None = None
    take_profit_price: float | None = None
    bars_held: int = 0


@dataclass(frozen=True)
class Trade:
    instrument: Instrument
    direction: PositionDirection
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    units: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    bars_held: int
    exit_reason: ExitReason
    entry_commission: float = 0.0
    exit_commission: float = 0.0
    entry_signal: SignalEvent | None = None
    exit_signal: SignalEvent | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    equity: float
    cash: float
    unrealized_pnl: float
    drawdown_pct: float


@dataclass(frozen=True)
class BacktestSummary:
    initial_capital: float
    final_equity: float
    total_gross_pnl: float
    total_net_pnl: float
    total_fees: float
    total_return_pct: float
    annualized_return_pct: float | None
    max_drawdown_pct: float
    total_trades: int
    win_rate_pct: float
    avg_trade_return_pct: float
    avg_trade_net_pnl: float
    profit_factor: float | None
    sharpe_ratio: float | None


@dataclass(frozen=True)
class BacktestResult:
    config: BacktestConfig
    instrument: Instrument
    interval: BarInterval
    trades: tuple[Trade, ...]
    equity_curve: tuple[EquityPoint, ...]
    summary: BacktestSummary
    signal_events: tuple[SignalEvent, ...]
    diagnostics: Mapping[str, Any] = field(default_factory=dict)
