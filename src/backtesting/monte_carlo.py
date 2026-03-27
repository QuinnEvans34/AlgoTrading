"""Optional Monte Carlo helpers for trade-sequence robustness checks."""

from __future__ import annotations

from dataclasses import dataclass
import random
import statistics
from typing import Sequence

from .contracts import Trade


@dataclass(frozen=True)
class MonteCarloSummary:
    iterations: int
    pnl_mean: float
    pnl_std: float
    drawdown_mean: float
    drawdown_std: float


def bootstrap_trade_pnl(
    trades: Sequence[Trade],
    *,
    iterations: int = 500,
    seed: int = 7,
) -> MonteCarloSummary | None:
    if not trades:
        return None
    rng = random.Random(seed)
    pnls: list[float] = []
    drawdowns: list[float] = []
    pnl_values = [t.net_pnl for t in trades]

    for _ in range(iterations):
        sample = [rng.choice(pnl_values) for _ in pnl_values]
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for pnl in sample:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        pnls.append(cumulative)
        drawdowns.append(max_drawdown)

    pnl_std = statistics.stdev(pnls) if len(pnls) > 1 else 0.0
    dd_std = statistics.stdev(drawdowns) if len(drawdowns) > 1 else 0.0
    return MonteCarloSummary(
        iterations=iterations,
        pnl_mean=statistics.fmean(pnls),
        pnl_std=pnl_std,
        drawdown_mean=statistics.fmean(drawdowns),
        drawdown_std=dd_std,
    )
