import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import BacktestConfig, BacktestInput, BacktestSimulator  # noqa: E402
from diagnostics import (  # noqa: E402
    DiagnosticEquityPoint,
    DiagnosticsInput,
    build_report,
    build_report_from_backtest,
)
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from strategy_engine.contracts import StrategyEvaluation, StrategyInput  # noqa: E402
from strategy_engine.strategies.base import Strategy  # noqa: E402


class NoSignalStrategy(Strategy):
    @property
    def name(self) -> str:
        return "no_signal_strategy"

    def evaluate(self, strategy_input: StrategyInput) -> StrategyEvaluation:
        return StrategyEvaluation(
            strategy_name=self.name,
            instrument=strategy_input.instrument,
            interval=strategy_input.interval,
            candle_count=len(strategy_input.candles),
            signal=None,
        )


def make_candles(values: list[float]) -> tuple[Candle, ...]:
    ts = datetime(2026, 2, 1, tzinfo=timezone.utc)
    out: list[Candle] = []
    for value in values:
        out.append(
            Candle(
                timestamp=ts,
                open=value,
                high=value + 0.3,
                low=value - 0.3,
                close=value + 0.1,
                volume=500.0,
            )
        )
        ts += timedelta(minutes=1)
    return tuple(out)


class DiagnosticsEdgeCaseTests(unittest.TestCase):
    def test_zero_trade_run(self) -> None:
        instrument = Instrument(symbol="MSFT", asset_class=AssetClass.STOCK)
        simulator = BacktestSimulator()
        strategy = NoSignalStrategy()
        result = simulator.run(
            backtest_input=BacktestInput(
                instrument=instrument,
                interval=BarInterval.M1,
                candles=make_candles([100, 101, 102, 103, 104, 105]),
            ),
            strategy=strategy,
            config=BacktestConfig(warmup_bars=1),
        )

        report = build_report_from_backtest(result)
        self.assertEqual(report.trade_analysis.trade_count, 0)
        self.assertIsNone(report.trade_analysis.win_rate_pct)
        self.assertIsNone(report.trade_analysis.expectancy_net_pnl)
        self.assertEqual(report.risk.max_drawdown_pct, 0.0)
        self.assertEqual(len(report.drawdown_episodes), 0)

    def test_tiny_sample_metrics_guard(self) -> None:
        instrument = Instrument(symbol="SPY", asset_class=AssetClass.STOCK)
        ts = datetime(2026, 3, 1, tzinfo=timezone.utc)
        diagnostics_input = DiagnosticsInput(
            run_id="tiny-sample",
            run_name="Tiny Sample",
            instrument=instrument,
            interval=BarInterval.D1,
            initial_capital=1000.0,
            trades=(),
            equity_curve=(
                DiagnosticEquityPoint(
                    timestamp=ts,
                    equity=1000.0,
                    cash=1000.0,
                    unrealized_pnl=0.0,
                    drawdown_pct=0.0,
                ),
            ),
        )
        report = build_report(diagnostics_input)
        self.assertIsNone(report.performance.annualized_return_pct)
        self.assertIsNone(report.risk.volatility_pct)
        self.assertIsNone(report.risk.sharpe_ratio)
        self.assertEqual(report.performance.total_return_pct, 0.0)


if __name__ == "__main__":
    unittest.main()

