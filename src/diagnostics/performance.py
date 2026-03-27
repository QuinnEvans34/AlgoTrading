"""Run-level performance metric calculations."""

from __future__ import annotations

from .contracts import DiagnosticsConfig, DiagnosticsInput, PerformanceMetrics


def bars_per_year_for_interval(config: DiagnosticsConfig, interval) -> int | None:
    bars_per_year = config.bars_per_year.get(interval)
    if bars_per_year is None or bars_per_year <= 0:
        return None
    return bars_per_year


def annualized_return_pct(
    *,
    initial_capital: float,
    final_equity: float,
    periods: int,
    bars_per_year: int | None,
    annualize_returns: bool,
    min_periods_for_annualization: int,
    min_years_for_annualization: float,
) -> float | None:
    if not annualize_returns:
        return None
    if bars_per_year is None:
        return None
    if periods < min_periods_for_annualization:
        return None
    if initial_capital <= 0 or final_equity <= 0:
        return None

    years = periods / bars_per_year
    if years <= 0:
        return None
    if years < min_years_for_annualization:
        return None

    growth = final_equity / initial_capital
    return ((growth ** (1.0 / years)) - 1.0) * 100.0


def compute_performance(
    diagnostics_input: DiagnosticsInput,
    config: DiagnosticsConfig,
) -> PerformanceMetrics:
    trades = diagnostics_input.trades
    curve = diagnostics_input.equity_curve
    initial_capital = diagnostics_input.initial_capital
    final_equity = curve[-1].equity if curve else initial_capital

    total_gross_pnl = sum(trade.gross_pnl for trade in trades)
    total_net_pnl = sum(trade.net_pnl for trade in trades)
    total_commissions = sum(
        (trade.entry_commission + trade.exit_commission) for trade in trades
    )
    total_return_pct = (
        ((final_equity - initial_capital) / initial_capital) * 100.0
        if initial_capital > 0
        else 0.0
    )

    bars_per_year = bars_per_year_for_interval(config, diagnostics_input.interval)
    annualized_return = annualized_return_pct(
        initial_capital=initial_capital,
        final_equity=final_equity,
        periods=max(0, len(curve) - 1),
        bars_per_year=bars_per_year,
        annualize_returns=config.annualize_returns,
        min_periods_for_annualization=config.min_periods_for_annualization,
        min_years_for_annualization=config.min_years_for_annualization,
    )

    total_bars = max(0, len(curve) - 1)
    bars_in_market = sum(max(0, trade.bars_held) for trade in trades)
    exposure_pct = (
        min(100.0, (bars_in_market / total_bars) * 100.0) if total_bars > 0 else 0.0
    )

    return PerformanceMetrics(
        initial_capital=initial_capital,
        final_equity=final_equity,
        total_gross_pnl=total_gross_pnl,
        total_net_pnl=total_net_pnl,
        total_commissions=total_commissions,
        total_return_pct=total_return_pct,
        annualized_return_pct=annualized_return,
        trade_count=len(trades),
        exposure_pct=exposure_pct,
    )
