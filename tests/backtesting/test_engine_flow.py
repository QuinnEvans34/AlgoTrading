import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import (  # noqa: E402
    BacktestConfig,
    BacktestInput,
    BacktestSimulator,
    ExitReason,
    RiskExitConfig,
)
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
        return "sequence_strategy"

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
                diagnostics={"idx": idx},
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
            rationale=("sequence",),
            indicators={"seed": float(idx)},
        )
        return StrategyEvaluation(
            strategy_name=self.name,
            instrument=strategy_input.instrument,
            interval=strategy_input.interval,
            candle_count=len(strategy_input.candles),
            signal=signal,
        )


def make_candles(opens: list[float], highs: list[float], lows: list[float], closes: list[float]) -> tuple[Candle, ...]:
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out: list[Candle] = []
    for o, h, l, c in zip(opens, highs, lows, closes, strict=True):
        out.append(
            Candle(
                timestamp=ts,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=1000.0,
            )
        )
        ts += timedelta(minutes=1)
    return tuple(out)


class EngineFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        self.simulator = BacktestSimulator()

    def test_flip_and_end_close(self) -> None:
        candles = make_candles(
            opens=[100, 101, 102, 103, 104, 105, 106, 107, 108],
            highs=[101, 102, 103, 104, 105, 106, 107, 108, 109],
            lows=[99, 100, 101, 102, 103, 104, 105, 106, 107],
            closes=[100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5],
        )
        strategy = SequenceStrategy(
            by_index={
                2: (SignalDirection.BUY, 0.9),
                5: (SignalDirection.SELL, 0.9),
            }
        )
        result = self.simulator.run(
            backtest_input=BacktestInput(
                instrument=self.instrument,
                interval=BarInterval.M1,
                candles=candles,
            ),
            strategy=strategy,
            config=BacktestConfig(warmup_bars=1, allow_short=True, allow_flip=True),
        )
        self.assertEqual(len(result.trades), 2)
        self.assertEqual(result.trades[0].exit_reason, ExitReason.SIGNAL_FLIP)
        self.assertEqual(result.trades[1].exit_reason, ExitReason.END_OF_DATA)

    def test_confidence_threshold_filter(self) -> None:
        candles = make_candles(
            opens=[100, 101, 102, 103, 104],
            highs=[101, 102, 103, 104, 105],
            lows=[99, 100, 101, 102, 103],
            closes=[100, 101, 102, 103, 104],
        )
        strategy = SequenceStrategy(by_index={2: (SignalDirection.BUY, 0.2)})
        result = self.simulator.run(
            backtest_input=BacktestInput(
                instrument=self.instrument,
                interval=BarInterval.M1,
                candles=candles,
            ),
            strategy=strategy,
            config=BacktestConfig(warmup_bars=1, min_signal_confidence=0.5),
        )
        self.assertEqual(len(result.trades), 0)
        self.assertGreater(result.diagnostics["ignored_low_confidence_signals"], 0)

    def test_intrabar_conflict_uses_adverse_exit(self) -> None:
        candles = make_candles(
            opens=[100, 100, 100, 100],
            highs=[100.5, 100.5, 101.5, 100.2],
            lows=[99.5, 99.5, 98.5, 99.8],
            closes=[100, 100, 100, 100],
        )
        strategy = SequenceStrategy(by_index={1: (SignalDirection.BUY, 0.9)})
        result = self.simulator.run(
            backtest_input=BacktestInput(
                instrument=self.instrument,
                interval=BarInterval.M1,
                candles=candles,
            ),
            strategy=strategy,
            config=BacktestConfig(
                warmup_bars=1,
                risk_exits=RiskExitConfig(stop_loss_fraction=0.01, take_profit_fraction=0.01),
            ),
        )
        self.assertEqual(len(result.trades), 1)
        trade = result.trades[0]
        self.assertEqual(trade.exit_reason, ExitReason.STOP_LOSS)
        self.assertAlmostEqual(trade.exit_price, 99.0, places=6)

    def test_gap_through_stop_fills_at_open(self) -> None:
        candles = make_candles(
            opens=[100, 100, 95, 93],
            highs=[100.5, 100.5, 96, 94],
            lows=[99.5, 99.5, 94.2, 92],
            closes=[100, 100, 95, 93.5],
        )
        strategy = SequenceStrategy(by_index={1: (SignalDirection.BUY, 0.9)})
        result = self.simulator.run(
            backtest_input=BacktestInput(
                instrument=self.instrument,
                interval=BarInterval.M1,
                candles=candles,
            ),
            strategy=strategy,
            config=BacktestConfig(
                warmup_bars=1,
                risk_exits=RiskExitConfig(stop_loss_fraction=0.01),
            ),
        )
        self.assertEqual(len(result.trades), 1)
        self.assertEqual(result.trades[0].exit_reason, ExitReason.STOP_LOSS)
        self.assertAlmostEqual(result.trades[0].exit_price, 93.0, places=6)

    def test_timed_exit(self) -> None:
        candles = make_candles(
            opens=[100, 101, 102, 103, 104, 105],
            highs=[101, 102, 103, 104, 105, 106],
            lows=[99, 100, 101, 102, 103, 104],
            closes=[100, 101, 102, 103, 104, 105],
        )
        strategy = SequenceStrategy(by_index={1: (SignalDirection.BUY, 0.9)})
        result = self.simulator.run(
            backtest_input=BacktestInput(
                instrument=self.instrument,
                interval=BarInterval.M1,
                candles=candles,
            ),
            strategy=strategy,
            config=BacktestConfig(
                warmup_bars=1,
                max_bars_in_position=1,
            ),
        )
        self.assertEqual(len(result.trades), 1)
        self.assertEqual(result.trades[0].exit_reason, ExitReason.MAX_BARS_TIMEOUT)
        self.assertGreater(result.diagnostics["timed_exits"], 0)


if __name__ == "__main__":
    unittest.main()
