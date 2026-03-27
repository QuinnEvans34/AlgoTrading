"""Trade-level diagnostics and distribution metrics."""

from __future__ import annotations

import statistics
from typing import Sequence

from .contracts import (
    DiagnosticTrade,
    SideBreakdown,
    TradeAnalytics,
    TradeAnnotation,
)


def _side_breakdown(side: str, trades: Sequence[DiagnosticTrade]) -> SideBreakdown:
    side_trades = [t for t in trades if t.direction == side]
    if not side_trades:
        return SideBreakdown(
            side=side,
            trade_count=0,
            net_pnl=0.0,
            win_rate_pct=None,
            avg_return_pct=None,
        )
    win_count = sum(1 for t in side_trades if t.net_pnl > 0)
    win_rate_pct = (win_count / len(side_trades)) * 100.0
    avg_return_pct = statistics.fmean(t.return_pct for t in side_trades)
    net_pnl = sum(t.net_pnl for t in side_trades)
    return SideBreakdown(
        side=side,
        trade_count=len(side_trades),
        net_pnl=net_pnl,
        win_rate_pct=win_rate_pct,
        avg_return_pct=avg_return_pct,
    )


def _max_streaks(trades: Sequence[DiagnosticTrade]) -> tuple[int, int]:
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0
    for trade in trades:
        if trade.net_pnl > 0:
            current_win_streak += 1
            current_loss_streak = 0
        elif trade.net_pnl < 0:
            current_loss_streak += 1
            current_win_streak = 0
        else:
            current_win_streak = 0
            current_loss_streak = 0
        if current_win_streak > max_win_streak:
            max_win_streak = current_win_streak
        if current_loss_streak > max_loss_streak:
            max_loss_streak = current_loss_streak
    return max_win_streak, max_loss_streak


def _annotation_rows(
    trades: Sequence[DiagnosticTrade],
    *,
    limit: int,
    descending: bool,
) -> tuple[TradeAnnotation, ...]:
    if limit <= 0:
        return ()
    sorted_rows = sorted(trades, key=lambda t: t.net_pnl, reverse=descending)[:limit]
    return tuple(
        TradeAnnotation(
            direction=trade.direction,
            entry_time=trade.entry_time,
            exit_time=trade.exit_time,
            net_pnl=trade.net_pnl,
            return_pct=trade.return_pct,
            bars_held=trade.bars_held,
            exit_reason=trade.exit_reason,
        )
        for trade in sorted_rows
    )


def compute_trade_analytics(
    trades: Sequence[DiagnosticTrade],
    *,
    top_trade_annotations: int,
) -> TradeAnalytics:
    trade_count = len(trades)
    if trade_count == 0:
        empty_side_long = SideBreakdown(
            side="long",
            trade_count=0,
            net_pnl=0.0,
            win_rate_pct=None,
            avg_return_pct=None,
        )
        empty_side_short = SideBreakdown(
            side="short",
            trade_count=0,
            net_pnl=0.0,
            win_rate_pct=None,
            avg_return_pct=None,
        )
        return TradeAnalytics(
            trade_count=0,
            win_count=0,
            loss_count=0,
            flat_count=0,
            win_rate_pct=None,
            expectancy_net_pnl=None,
            expectancy_return_pct=None,
            avg_win_net_pnl=None,
            avg_loss_net_pnl=None,
            avg_win_return_pct=None,
            avg_loss_return_pct=None,
            median_trade_net_pnl=None,
            median_trade_return_pct=None,
            largest_win_net_pnl=None,
            largest_loss_net_pnl=None,
            profit_factor=None,
            payoff_ratio=None,
            avg_bars_held=None,
            median_bars_held=None,
            max_win_streak=0,
            max_loss_streak=0,
            long_side=empty_side_long,
            short_side=empty_side_short,
            top_winning_trades=(),
            top_losing_trades=(),
        )

    wins = [trade for trade in trades if trade.net_pnl > 0]
    losses = [trade for trade in trades if trade.net_pnl < 0]
    flat = [trade for trade in trades if trade.net_pnl == 0]

    win_count = len(wins)
    loss_count = len(losses)
    flat_count = len(flat)
    win_rate_pct = (win_count / trade_count) * 100.0

    expectancy_net_pnl = statistics.fmean(trade.net_pnl for trade in trades)
    expectancy_return_pct = statistics.fmean(trade.return_pct for trade in trades)

    avg_win_net_pnl = statistics.fmean(t.net_pnl for t in wins) if wins else None
    avg_loss_net_pnl = statistics.fmean(t.net_pnl for t in losses) if losses else None
    avg_win_return_pct = statistics.fmean(t.return_pct for t in wins) if wins else None
    avg_loss_return_pct = (
        statistics.fmean(t.return_pct for t in losses) if losses else None
    )

    median_trade_net_pnl = statistics.median(trade.net_pnl for trade in trades)
    median_trade_return_pct = statistics.median(trade.return_pct for trade in trades)
    largest_win_net_pnl = max((trade.net_pnl for trade in trades), default=None)
    largest_loss_net_pnl = min((trade.net_pnl for trade in trades), default=None)

    gross_profit = sum(t.net_pnl for t in wins)
    gross_loss = abs(sum(t.net_pnl for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

    payoff_ratio = None
    if avg_win_net_pnl is not None and avg_loss_net_pnl is not None and avg_loss_net_pnl != 0:
        payoff_ratio = avg_win_net_pnl / abs(avg_loss_net_pnl)

    avg_bars_held = statistics.fmean(trade.bars_held for trade in trades)
    median_bars_held = statistics.median(trade.bars_held for trade in trades)
    max_win_streak, max_loss_streak = _max_streaks(trades)

    long_side = _side_breakdown("long", trades)
    short_side = _side_breakdown("short", trades)

    top_winning_trades = _annotation_rows(
        trades,
        limit=top_trade_annotations,
        descending=True,
    )
    top_losing_trades = _annotation_rows(
        trades,
        limit=top_trade_annotations,
        descending=False,
    )

    return TradeAnalytics(
        trade_count=trade_count,
        win_count=win_count,
        loss_count=loss_count,
        flat_count=flat_count,
        win_rate_pct=win_rate_pct,
        expectancy_net_pnl=expectancy_net_pnl,
        expectancy_return_pct=expectancy_return_pct,
        avg_win_net_pnl=avg_win_net_pnl,
        avg_loss_net_pnl=avg_loss_net_pnl,
        avg_win_return_pct=avg_win_return_pct,
        avg_loss_return_pct=avg_loss_return_pct,
        median_trade_net_pnl=median_trade_net_pnl,
        median_trade_return_pct=median_trade_return_pct,
        largest_win_net_pnl=largest_win_net_pnl,
        largest_loss_net_pnl=largest_loss_net_pnl,
        profit_factor=profit_factor,
        payoff_ratio=payoff_ratio,
        avg_bars_held=avg_bars_held,
        median_bars_held=median_bars_held,
        max_win_streak=max_win_streak,
        max_loss_streak=max_loss_streak,
        long_side=long_side,
        short_side=short_side,
        top_winning_trades=top_winning_trades,
        top_losing_trades=top_losing_trades,
    )

