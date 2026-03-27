"""Risk, drawdown, and return-series diagnostics."""

from __future__ import annotations

import math
import statistics
from typing import Sequence

from .contracts import (
    DiagnosticEquityPoint,
    DiagnosticsConfig,
    DrawdownEpisode,
    DrawdownPoint,
    ReturnPoint,
    RiskAnalytics,
)
from .performance import bars_per_year_for_interval


def build_return_series(
    equity_curve: Sequence[DiagnosticEquityPoint],
) -> tuple[ReturnPoint, ...]:
    if len(equity_curve) < 2:
        return ()
    points: list[ReturnPoint] = []
    for idx in range(1, len(equity_curve)):
        prev = equity_curve[idx - 1].equity
        curr = equity_curve[idx].equity
        ret = ((curr - prev) / prev) if prev > 0 else 0.0
        points.append(
            ReturnPoint(
                timestamp=equity_curve[idx].timestamp,
                return_fraction=ret,
            )
        )
    return tuple(points)


def build_drawdown_series(
    equity_curve: Sequence[DiagnosticEquityPoint],
) -> tuple[DrawdownPoint, ...]:
    if not equity_curve:
        return ()
    peak = equity_curve[0].equity
    rows: list[DrawdownPoint] = []
    for point in equity_curve:
        if point.equity > peak:
            peak = point.equity
        drawdown_pct = ((peak - point.equity) / peak * 100.0) if peak > 0 else 0.0
        rows.append(DrawdownPoint(timestamp=point.timestamp, drawdown_pct=drawdown_pct))
    return tuple(rows)


def extract_drawdown_episodes(
    drawdown_series: Sequence[DrawdownPoint],
    *,
    max_episodes: int,
) -> tuple[DrawdownEpisode, ...]:
    if not drawdown_series:
        return ()

    episodes: list[DrawdownEpisode] = []
    active = False

    peak_time = drawdown_series[0].timestamp
    start_idx = 0
    trough_idx = 0
    trough_time = drawdown_series[0].timestamp
    depth_pct = 0.0

    for idx, point in enumerate(drawdown_series):
        if point.drawdown_pct <= 0:
            if active:
                duration = (idx - start_idx) + 1
                recovery_bars = idx - trough_idx
                episodes.append(
                    DrawdownEpisode(
                        peak_time=peak_time,
                        trough_time=trough_time,
                        recovery_time=point.timestamp,
                        depth_pct=depth_pct,
                        duration_bars=duration,
                        recovery_bars=recovery_bars,
                    )
                )
                active = False
            peak_time = point.timestamp
            continue

        if not active:
            active = True
            start_idx = idx
            trough_idx = idx
            trough_time = point.timestamp
            depth_pct = point.drawdown_pct
            continue

        if point.drawdown_pct > depth_pct:
            depth_pct = point.drawdown_pct
            trough_idx = idx
            trough_time = point.timestamp

    if active:
        duration = (len(drawdown_series) - start_idx)
        episodes.append(
            DrawdownEpisode(
                peak_time=peak_time,
                trough_time=trough_time,
                recovery_time=None,
                depth_pct=depth_pct,
                duration_bars=duration,
                recovery_bars=None,
            )
        )

    episodes.sort(key=lambda ep: ep.depth_pct, reverse=True)
    return tuple(episodes[:max_episodes])


def _per_bar_risk_free_rate(annual_risk_free_rate: float, bars_per_year: int) -> float:
    if bars_per_year <= 0:
        return 0.0
    return (1.0 + annual_risk_free_rate) ** (1.0 / bars_per_year) - 1.0


def _annualized_volatility(
    returns: Sequence[float],
    *,
    bars_per_year: int | None,
    min_periods: int,
) -> float | None:
    if bars_per_year is None or bars_per_year <= 0:
        return None
    if len(returns) < max(2, min_periods):
        return None
    std = statistics.stdev(returns)
    if std <= 0:
        return None
    return std * math.sqrt(bars_per_year) * 100.0


def _sharpe_ratio(
    returns: Sequence[float],
    *,
    annual_risk_free_rate: float,
    bars_per_year: int | None,
    min_periods: int,
) -> float | None:
    if bars_per_year is None or bars_per_year <= 0:
        return None
    if len(returns) < max(2, min_periods):
        return None
    rf_per_bar = _per_bar_risk_free_rate(annual_risk_free_rate, bars_per_year)
    excess = [ret - rf_per_bar for ret in returns]
    std = statistics.stdev(excess)
    if std <= 0:
        return None
    mean = statistics.fmean(excess)
    return (mean / std) * math.sqrt(bars_per_year)


def _sortino_ratio(
    returns: Sequence[float],
    *,
    annual_risk_free_rate: float,
    bars_per_year: int | None,
    min_periods: int,
) -> tuple[float | None, float | None]:
    if bars_per_year is None or bars_per_year <= 0:
        return None, None
    if len(returns) < max(2, min_periods):
        return None, None

    rf_per_bar = _per_bar_risk_free_rate(annual_risk_free_rate, bars_per_year)
    excess = [ret - rf_per_bar for ret in returns]
    downside_component = [min(0.0, value) for value in excess]
    downside_variance = sum(value * value for value in downside_component) / len(excess)
    downside_dev = math.sqrt(downside_variance)

    downside_vol_pct = (
        downside_dev * math.sqrt(bars_per_year) * 100.0 if downside_dev > 0 else None
    )
    if downside_dev <= 0:
        return None, downside_vol_pct

    mean_excess = statistics.fmean(excess)
    sortino = (mean_excess / downside_dev) * math.sqrt(bars_per_year)
    return sortino, downside_vol_pct


def compute_risk_analytics(
    *,
    equity_curve: Sequence[DiagnosticEquityPoint],
    interval,
    config: DiagnosticsConfig,
    annualized_return_pct: float | None,
) -> tuple[
    RiskAnalytics,
    tuple[ReturnPoint, ...],
    tuple[DrawdownPoint, ...],
    tuple[DrawdownEpisode, ...],
]:
    drawdown_series = build_drawdown_series(equity_curve)
    all_episodes = extract_drawdown_episodes(
        drawdown_series,
        max_episodes=config.max_drawdown_episodes,
    )
    return_series = build_return_series(equity_curve)
    returns = [point.return_fraction for point in return_series]

    max_drawdown_pct = max((point.drawdown_pct for point in drawdown_series), default=0.0)
    max_drawdown_duration_bars = max(
        (episode.duration_bars for episode in all_episodes),
        default=0,
    )

    bars_per_year = bars_per_year_for_interval(config, interval)
    volatility_pct = _annualized_volatility(
        returns,
        bars_per_year=bars_per_year,
        min_periods=config.min_periods_for_risk_metrics,
    )
    sharpe_ratio = _sharpe_ratio(
        returns,
        annual_risk_free_rate=config.annual_risk_free_rate,
        bars_per_year=bars_per_year,
        min_periods=config.min_periods_for_risk_metrics,
    )
    sortino_ratio, downside_volatility_pct = _sortino_ratio(
        returns,
        annual_risk_free_rate=config.annual_risk_free_rate,
        bars_per_year=bars_per_year,
        min_periods=config.min_periods_for_risk_metrics,
    )

    calmar_ratio = None
    if annualized_return_pct is not None and max_drawdown_pct > 0:
        calmar_ratio = annualized_return_pct / max_drawdown_pct

    analytics = RiskAnalytics(
        max_drawdown_pct=max_drawdown_pct,
        max_drawdown_duration_bars=max_drawdown_duration_bars,
        volatility_pct=volatility_pct,
        downside_volatility_pct=downside_volatility_pct,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
    )
    return analytics, return_series, drawdown_series, all_episodes

