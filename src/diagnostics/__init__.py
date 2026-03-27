"""Diagnostics and performance analytics subsystem."""

from .adapters import from_backtest_result
from .contracts import (
    DiagnosticEquityPoint,
    DiagnosticSignalEvent,
    DiagnosticTrade,
    DiagnosticsConfig,
    DiagnosticsInput,
    DiagnosticsReport,
    DrawdownEpisode,
    DrawdownPoint,
    PerformanceMetrics,
    ReturnPoint,
    RiskAnalytics,
    RunComparisonSnapshot,
    SeriesArtifacts,
    SideBreakdown,
    TradeAnalytics,
    TradeAnnotation,
)
from .performance import annualized_return_pct, bars_per_year_for_interval, compute_performance
from .report import build_report, build_report_from_backtest
from .risk import build_drawdown_series, build_return_series, compute_risk_analytics
from .trade_analysis import compute_trade_analytics

__all__ = [
    "DiagnosticsConfig",
    "DiagnosticsInput",
    "DiagnosticTrade",
    "DiagnosticEquityPoint",
    "DiagnosticSignalEvent",
    "PerformanceMetrics",
    "TradeAnalytics",
    "RiskAnalytics",
    "DrawdownEpisode",
    "DrawdownPoint",
    "ReturnPoint",
    "SeriesArtifacts",
    "RunComparisonSnapshot",
    "TradeAnnotation",
    "SideBreakdown",
    "DiagnosticsReport",
    "from_backtest_result",
    "bars_per_year_for_interval",
    "annualized_return_pct",
    "compute_performance",
    "compute_trade_analytics",
    "build_return_series",
    "build_drawdown_series",
    "compute_risk_analytics",
    "build_report",
    "build_report_from_backtest",
]

