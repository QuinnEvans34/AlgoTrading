"""Typed contracts for diagnostics and performance analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from market_data.contracts import BarInterval, Instrument


def default_bars_per_year() -> dict[BarInterval, int]:
    """Default annualization assumptions aligned to the backtesting layer."""
    return {
        BarInterval.M1: 252 * 390,
        BarInterval.M5: 252 * 78,
        BarInterval.M15: 252 * 26,
        BarInterval.M30: 252 * 13,
        BarInterval.H1: 252 * 6,
        BarInterval.H4: 252 * 2,
        BarInterval.D1: 252,
    }


@dataclass(frozen=True)
class DiagnosticsConfig:
    bars_per_year: Mapping[BarInterval, int] = field(default_factory=default_bars_per_year)
    annualize_returns: bool = True
    annual_risk_free_rate: float = 0.0
    min_periods_for_annualization: int = 2
    min_years_for_annualization: float = 1.0 / 12.0
    min_periods_for_risk_metrics: int = 2
    top_trade_annotations: int = 5
    max_drawdown_episodes: int = 10


@dataclass(frozen=True)
class DiagnosticTrade:
    direction: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    units: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    bars_held: int
    entry_commission: float
    exit_commission: float
    exit_reason: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiagnosticEquityPoint:
    timestamp: datetime
    equity: float
    cash: float
    unrealized_pnl: float
    drawdown_pct: float = 0.0


@dataclass(frozen=True)
class DiagnosticSignalEvent:
    timestamp: datetime
    direction: str
    confidence: float
    score: float
    rationale: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DiagnosticsInput:
    run_id: str | None
    run_name: str | None
    instrument: Instrument
    interval: BarInterval
    initial_capital: float
    trades: tuple[DiagnosticTrade, ...]
    equity_curve: tuple[DiagnosticEquityPoint, ...]
    signal_events: tuple[DiagnosticSignalEvent, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PerformanceMetrics:
    initial_capital: float
    final_equity: float
    total_gross_pnl: float
    total_net_pnl: float
    total_commissions: float
    total_return_pct: float
    annualized_return_pct: float | None
    trade_count: int
    exposure_pct: float


@dataclass(frozen=True)
class SideBreakdown:
    side: str
    trade_count: int
    net_pnl: float
    win_rate_pct: float | None
    avg_return_pct: float | None


@dataclass(frozen=True)
class TradeAnnotation:
    direction: str
    entry_time: datetime
    exit_time: datetime
    net_pnl: float
    return_pct: float
    bars_held: int
    exit_reason: str


@dataclass(frozen=True)
class TradeAnalytics:
    trade_count: int
    win_count: int
    loss_count: int
    flat_count: int
    win_rate_pct: float | None
    expectancy_net_pnl: float | None
    expectancy_return_pct: float | None
    avg_win_net_pnl: float | None
    avg_loss_net_pnl: float | None
    avg_win_return_pct: float | None
    avg_loss_return_pct: float | None
    median_trade_net_pnl: float | None
    median_trade_return_pct: float | None
    largest_win_net_pnl: float | None
    largest_loss_net_pnl: float | None
    profit_factor: float | None
    payoff_ratio: float | None
    avg_bars_held: float | None
    median_bars_held: float | None
    max_win_streak: int
    max_loss_streak: int
    long_side: SideBreakdown
    short_side: SideBreakdown
    top_winning_trades: tuple[TradeAnnotation, ...]
    top_losing_trades: tuple[TradeAnnotation, ...]


@dataclass(frozen=True)
class RiskAnalytics:
    max_drawdown_pct: float
    max_drawdown_duration_bars: int
    volatility_pct: float | None
    downside_volatility_pct: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None


@dataclass(frozen=True)
class ReturnPoint:
    timestamp: datetime
    return_fraction: float


@dataclass(frozen=True)
class DrawdownPoint:
    timestamp: datetime
    drawdown_pct: float


@dataclass(frozen=True)
class DrawdownEpisode:
    peak_time: datetime
    trough_time: datetime
    recovery_time: datetime | None
    depth_pct: float
    duration_bars: int
    recovery_bars: int | None


@dataclass(frozen=True)
class SeriesArtifacts:
    equity_curve: tuple[DiagnosticEquityPoint, ...]
    return_series: tuple[ReturnPoint, ...]
    drawdown_series: tuple[DrawdownPoint, ...]
    trade_net_pnls: tuple[float, ...]
    trade_return_pcts: tuple[float, ...]
    trade_durations_bars: tuple[int, ...]


@dataclass(frozen=True)
class RunComparisonSnapshot:
    run_id: str | None
    run_name: str | None
    instrument_symbol: str
    interval: BarInterval
    total_return_pct: float
    annualized_return_pct: float | None
    max_drawdown_pct: float
    sharpe_ratio: float | None
    total_trades: int
    win_rate_pct: float | None
    total_net_pnl: float


@dataclass(frozen=True)
class DiagnosticsReport:
    run_id: str | None
    run_name: str | None
    instrument: Instrument
    interval: BarInterval
    performance: PerformanceMetrics
    trade_analysis: TradeAnalytics
    risk: RiskAnalytics
    drawdown_episodes: tuple[DrawdownEpisode, ...]
    series: SeriesArtifacts
    comparison_snapshot: RunComparisonSnapshot
    assumptions: Mapping[str, str]
    metadata: Mapping[str, Any] = field(default_factory=dict)
