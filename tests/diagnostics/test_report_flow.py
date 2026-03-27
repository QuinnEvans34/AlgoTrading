import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import BacktestConfig, BacktestInput, BacktestSimulator  # noqa: E402
from diagnostics import build_report_from_backtest  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from strategy_engine.contracts import (  # noqa: E402
    SignalDirection,
    StrategyEvaluation,
    StrategyInput,
    StrategySignal,
)
from strategy_engine.strategies.base import Strategy  # noqa: E402


class SequenceStrategy(Strategy):
    def __init__(self, by_index: dict[int, tuple[SignalDirection, float]]) -> None:
        self._by_index = by_index

    @property
    def name(self) -> str:
        return "sequence_strategy_for_diagnostics"

    def evaluate(self, strategy_input: StrategyInput) -> StrategyEvaluation:
        idx = len(strategy_input.candles) - 1
        signal_tuple = self._by_index.get(idx)
        if signal_tuple is None:
            return StrategyEvaluation(
                strategy_name=self.name,
                instrument=strategy_input.instrument,
                interval=strategy_input.interval,
                candle_count=len(strategy_input.candles),
                signal=None,
            )
        direction, confidence = signal_tuple
        signal = StrategySignal(
            strategy_name=self.name,
            instrument=strategy_input.instrument,
            interval=strategy_input.interval,
            timestamp=strategy_input.candles[-1].timestamp,
            direction=direction,
            confidence=confidence,
            score=confidence,
            rationale=("unit-test",),
            indicators={},
        )
        return StrategyEvaluation(
            strategy_name=self.name,
            instrument=strategy_input.instrument,
            interval=strategy_input.interval,
            candle_count=len(strategy_input.candles),
            signal=signal,
        )


def make_candles(values: list[float]) -> tuple[Candle, ...]:
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out: list[Candle] = []
    for value in values:
        out.append(
            Candle(
                timestamp=ts,
                open=value,
                high=value + 0.5,
                low=value - 0.5,
                close=value + 0.2,
                volume=1000.0,
            )
        )
        ts += timedelta(minutes=1)
    return tuple(out)


class DiagnosticsReportFlowTests(unittest.TestCase):
    def test_backtest_to_report_flow(self) -> None:
        instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        simulator = BacktestSimulator()
        strategy = SequenceStrategy(
            by_index={
                2: (SignalDirection.BUY, 0.9),
                5: (SignalDirection.SELL, 0.9),
            }
        )

        result = simulator.run(
            backtest_input=BacktestInput(
                instrument=instrument,
                interval=BarInterval.M1,
                candles=make_candles([100, 101, 102, 103, 104, 103, 102, 101, 102, 103]),
            ),
            strategy=strategy,
            config=BacktestConfig(warmup_bars=1, allow_short=True, allow_flip=True),
        )
        report = build_report_from_backtest(
            result,
            run_id="ut-report-flow",
            run_name="Diagnostics Flow Test",
        )

        self.assertEqual(report.run_id, "ut-report-flow")
        self.assertEqual(report.instrument.symbol, "AAPL")
        self.assertGreaterEqual(report.performance.trade_count, 1)
        self.assertEqual(report.trade_analysis.trade_count, len(result.trades))
        self.assertEqual(len(report.series.equity_curve), len(result.equity_curve))
        self.assertEqual(len(report.series.drawdown_series), len(result.equity_curve))
        self.assertEqual(
            len(report.series.return_series),
            max(0, len(result.equity_curve) - 1),
        )
        self.assertGreaterEqual(report.risk.max_drawdown_pct, 0.0)
        self.assertIn("return_basis", report.assumptions)
        self.assertEqual(report.comparison_snapshot.run_name, "Diagnostics Flow Test")


if __name__ == "__main__":
    unittest.main()

