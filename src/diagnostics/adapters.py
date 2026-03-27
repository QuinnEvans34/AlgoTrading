"""Adapters that convert simulator outputs into diagnostics inputs."""

from __future__ import annotations

from typing import Any, Mapping

from backtesting.contracts import BacktestResult

from .contracts import (
    DiagnosticEquityPoint,
    DiagnosticSignalEvent,
    DiagnosticTrade,
    DiagnosticsInput,
)


def from_backtest_result(
    backtest_result: BacktestResult,
    *,
    run_id: str | None = None,
    run_name: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DiagnosticsInput:
    """Map ``BacktestResult`` to a provider-neutral diagnostics input contract."""
    trade_rows = tuple(
        DiagnosticTrade(
            direction=trade.direction.value,
            entry_time=trade.entry_time,
            exit_time=trade.exit_time,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            units=trade.units,
            gross_pnl=trade.gross_pnl,
            net_pnl=trade.net_pnl,
            return_pct=trade.return_pct,
            bars_held=trade.bars_held,
            entry_commission=trade.entry_commission,
            exit_commission=trade.exit_commission,
            exit_reason=trade.exit_reason.value,
            metadata=dict(trade.metadata),
        )
        for trade in backtest_result.trades
    )

    equity_rows = tuple(
        DiagnosticEquityPoint(
            timestamp=point.timestamp,
            equity=point.equity,
            cash=point.cash,
            unrealized_pnl=point.unrealized_pnl,
            drawdown_pct=point.drawdown_pct,
        )
        for point in backtest_result.equity_curve
    )

    signal_rows = tuple(
        DiagnosticSignalEvent(
            timestamp=event.timestamp,
            direction=event.direction.value,
            confidence=event.confidence,
            score=event.score,
            rationale=event.rationale,
            metadata=dict(event.metadata),
        )
        for event in backtest_result.signal_events
    )

    combined_metadata: dict[str, Any] = dict(metadata or {})
    combined_metadata["backtest_diagnostics"] = dict(backtest_result.diagnostics)
    combined_metadata["backtest_summary"] = {
        "final_equity": backtest_result.summary.final_equity,
        "total_return_pct": backtest_result.summary.total_return_pct,
        "max_drawdown_pct": backtest_result.summary.max_drawdown_pct,
    }

    return DiagnosticsInput(
        run_id=run_id,
        run_name=run_name,
        instrument=backtest_result.instrument,
        interval=backtest_result.interval,
        initial_capital=backtest_result.config.initial_capital,
        trades=trade_rows,
        equity_curve=equity_rows,
        signal_events=signal_rows,
        metadata=combined_metadata,
    )

