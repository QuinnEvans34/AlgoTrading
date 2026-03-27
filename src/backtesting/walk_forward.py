"""Lightweight walk-forward scaffolding for later optimization workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from strategy_engine.strategies.base import Strategy

from .contracts import BacktestConfig, BacktestInput, BacktestResult
from .engine import BacktestSimulator


@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True)
class WalkForwardResult:
    windows: tuple[WalkForwardWindow, ...]
    out_of_sample_results: tuple[BacktestResult, ...]


def rolling_windows(
    *,
    total_bars: int,
    train_bars: int,
    test_bars: int,
    step_bars: int | None = None,
) -> tuple[WalkForwardWindow, ...]:
    if train_bars <= 0 or test_bars <= 0:
        raise ValueError("train_bars and test_bars must be > 0")
    if total_bars < (train_bars + test_bars):
        return tuple()

    step = step_bars or test_bars
    windows: list[WalkForwardWindow] = []
    train_start = 0
    while True:
        train_end = train_start + train_bars
        test_start = train_end
        test_end = test_start + test_bars
        if test_end > total_bars:
            break
        windows.append(
            WalkForwardWindow(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        train_start += step
    return tuple(windows)


class WalkForwardRunner:
    """Research scaffold.

    This intentionally does not optimize parameters yet; it simply defines clean
    out-of-sample execution boundaries so parameter search can be layered in later.
    """

    def __init__(self, simulator: BacktestSimulator) -> None:
        self._simulator = simulator

    def run(
        self,
        *,
        full_input: BacktestInput,
        strategy_factory: Callable[[BacktestInput], Strategy],
        config: BacktestConfig,
        windows: Sequence[WalkForwardWindow],
    ) -> WalkForwardResult:
        results: list[BacktestResult] = []
        total_bars = len(full_input.candles)
        for window in windows:
            if not (
                0 <= window.train_start < window.train_end <= total_bars
                and 0 <= window.test_start < window.test_end <= total_bars
            ):
                raise ValueError(f"Invalid walk-forward window: {window}")
            test_input = BacktestInput(
                instrument=full_input.instrument,
                interval=full_input.interval,
                candles=full_input.candles[window.test_start : window.test_end],
            )
            train_slice = BacktestInput(
                instrument=full_input.instrument,
                interval=full_input.interval,
                candles=full_input.candles[window.train_start : window.train_end],
            )
            strategy = strategy_factory(train_slice)
            results.append(
                self._simulator.run(
                    backtest_input=test_input,
                    strategy=strategy,
                    config=config,
                )
            )
        return WalkForwardResult(
            windows=tuple(windows),
            out_of_sample_results=tuple(results),
        )
