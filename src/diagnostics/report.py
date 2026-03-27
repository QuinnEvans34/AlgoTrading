"""Orchestration entrypoints for diagnostics report generation."""

from __future__ import annotations

from dataclasses import replace

from backtesting.contracts import BacktestResult

from .adapters import from_backtest_result
from .contracts import (
    DiagnosticsConfig,
    DiagnosticsInput,
    DiagnosticsReport,
    RunComparisonSnapshot,
    SeriesArtifacts,
)
from .performance import compute_performance
from .risk import compute_risk_analytics
from .trade_analysis import compute_trade_analytics


def _normalize_input(data: DiagnosticsInput) -> DiagnosticsInput:
    trades = tuple(sorted(data.trades, key=lambda trade: trade.exit_time))
    equity = tuple(sorted(data.equity_curve, key=lambda point: point.timestamp))
    signals = tuple(sorted(data.signal_events, key=lambda event: event.timestamp))
    return replace(data, trades=trades, equity_curve=equity, signal_events=signals)


def _validate_input(data: DiagnosticsInput) -> None:
    if data.initial_capital <= 0:
        raise ValueError("DiagnosticsInput.initial_capital must be > 0")
    if not data.equity_curve:
        raise ValueError("DiagnosticsInput.equity_curve cannot be empty")
    for trade in data.trades:
        if trade.exit_time < trade.entry_time:
            raise ValueError("Trade exit_time cannot be before entry_time")
        if trade.bars_held < 0:
            raise ValueError("Trade bars_held must be >= 0")


def build_report(
    diagnostics_input: DiagnosticsInput,
    *,
    config: DiagnosticsConfig | None = None,
) -> DiagnosticsReport:
    cfg = config or DiagnosticsConfig()
    data = _normalize_input(diagnostics_input)
    _validate_input(data)

    performance = compute_performance(data, cfg)
    trade_analysis = compute_trade_analytics(
        data.trades,
        top_trade_annotations=cfg.top_trade_annotations,
    )
    risk, return_series, drawdown_series, drawdown_episodes = compute_risk_analytics(
        equity_curve=data.equity_curve,
        interval=data.interval,
        config=cfg,
        annualized_return_pct=performance.annualized_return_pct,
    )
    series = SeriesArtifacts(
        equity_curve=data.equity_curve,
        return_series=return_series,
        drawdown_series=drawdown_series,
        trade_net_pnls=tuple(trade.net_pnl for trade in data.trades),
        trade_return_pcts=tuple(trade.return_pct for trade in data.trades),
        trade_durations_bars=tuple(trade.bars_held for trade in data.trades),
    )

    snapshot = RunComparisonSnapshot(
        run_id=data.run_id,
        run_name=data.run_name,
        instrument_symbol=data.instrument.symbol,
        interval=data.interval,
        total_return_pct=performance.total_return_pct,
        annualized_return_pct=performance.annualized_return_pct,
        max_drawdown_pct=risk.max_drawdown_pct,
        sharpe_ratio=risk.sharpe_ratio,
        total_trades=trade_analysis.trade_count,
        win_rate_pct=trade_analysis.win_rate_pct,
        total_net_pnl=performance.total_net_pnl,
    )

    assumptions = {
        "return_basis": "Arithmetic per-bar equity returns from normalized equity curve.",
        "annualization": "Uses interval bars/year map when sample size is sufficient.",
        "risk_free_rate": "Annual rate converted to per-bar rate for Sharpe/Sortino.",
        "cost_handling": "Commissions explicit; spread/slippage reflected implicitly in net outcomes.",
        "drawdown": "Recomputed from equity series for consistency.",
        "sample_guards": "Sparse samples produce None for unstable metrics.",
    }

    return DiagnosticsReport(
        run_id=data.run_id,
        run_name=data.run_name,
        instrument=data.instrument,
        interval=data.interval,
        performance=performance,
        trade_analysis=trade_analysis,
        risk=risk,
        drawdown_episodes=drawdown_episodes,
        series=series,
        comparison_snapshot=snapshot,
        assumptions=assumptions,
        metadata=data.metadata,
    )


def build_report_from_backtest(
    backtest_result: BacktestResult,
    *,
    config: DiagnosticsConfig | None = None,
    run_id: str | None = None,
    run_name: str | None = None,
) -> DiagnosticsReport:
    diagnostics_input = from_backtest_result(
        backtest_result,
        run_id=run_id,
        run_name=run_name,
    )
    return build_report(diagnostics_input, config=config)

