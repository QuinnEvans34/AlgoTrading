"""Backtest metric calculations."""

from __future__ import annotations

import math
import statistics
from typing import Sequence

from .contracts import BacktestSummary, EquityPoint, Trade


def build_summary(
    *,
    initial_capital: float,
    trades: Sequence[Trade],
    equity_curve: Sequence[EquityPoint],
    bars_per_year: int,
) -> BacktestSummary:
    final_equity = equity_curve[-1].equity if equity_curve else initial_capital
    total_gross_pnl = sum(t.gross_pnl for t in trades)
    total_net_pnl = sum(t.net_pnl for t in trades)
    total_fees = sum((t.entry_commission + t.exit_commission) for t in trades)
    total_return_pct = (
        ((final_equity - initial_capital) / initial_capital) * 100.0
        if initial_capital > 0
        else 0.0
    )
    annualized_return = _annualized_return_pct(
        initial_capital=initial_capital,
        final_equity=final_equity,
        periods=max(len(equity_curve) - 1, 0),
        periods_per_year=bars_per_year,
    )

    max_drawdown = _max_drawdown_pct(equity_curve)
    total_trades = len(trades)
    wins = [t for t in trades if t.net_pnl > 0]
    losses = [t for t in trades if t.net_pnl < 0]
    win_rate = ((len(wins) / total_trades) * 100.0) if total_trades > 0 else 0.0
    avg_trade_return = (
        statistics.fmean(t.return_pct for t in trades) if trades else 0.0
    )
    avg_trade_net_pnl = statistics.fmean(t.net_pnl for t in trades) if trades else 0.0

    gross_profit = sum(t.net_pnl for t in wins)
    gross_loss = abs(sum(t.net_pnl for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None
    sharpe = _sharpe_ratio(equity_curve, bars_per_year)

    return BacktestSummary(
        initial_capital=initial_capital,
        final_equity=final_equity,
        total_gross_pnl=total_gross_pnl,
        total_net_pnl=total_net_pnl,
        total_fees=total_fees,
        total_return_pct=total_return_pct,
        annualized_return_pct=annualized_return,
        max_drawdown_pct=max_drawdown,
        total_trades=total_trades,
        win_rate_pct=win_rate,
        avg_trade_return_pct=avg_trade_return,
        avg_trade_net_pnl=avg_trade_net_pnl,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe,
    )


def _annualized_return_pct(
    *,
    initial_capital: float,
    final_equity: float,
    periods: int,
    periods_per_year: int,
) -> float | None:
    if initial_capital <= 0 or periods <= 0 or periods_per_year <= 0:
        return None
    if final_equity <= 0:
        return None
    years = periods / periods_per_year
    if years <= 0:
        return None
    growth = final_equity / initial_capital
    return ((growth ** (1.0 / years)) - 1.0) * 100.0


def _max_drawdown_pct(equity_curve: Sequence[EquityPoint]) -> float:
    if not equity_curve:
        return 0.0
    return max((point.drawdown_pct for point in equity_curve), default=0.0)


def _sharpe_ratio(equity_curve: Sequence[EquityPoint], bars_per_year: int) -> float | None:
    if len(equity_curve) < 3:
        return None
    returns: list[float] = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1].equity
        curr = equity_curve[i].equity
        if prev <= 0:
            continue
        returns.append((curr - prev) / prev)
    if len(returns) < 2:
        return None
    std = statistics.stdev(returns)
    if std == 0:
        return None
    mean = statistics.fmean(returns)
    return (mean / std) * math.sqrt(bars_per_year)
