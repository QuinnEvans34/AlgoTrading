import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import BacktestConfig  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from ml_data import DirectionLabelSpec, FutureReturnLabelSpec  # noqa: E402
from modeling import ModelFamily, ModelSpec, TaskType  # noqa: E402
from research import (  # noqa: E402
    InlineCandleSource,
    MLWorkflowSpec,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    StrategyWorkflowSpec,
    compare_saved_runs,
)


def make_candles(count: int = 260) -> tuple[Candle, ...]:
    rows: list[Candle] = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + (0.1 if i % 3 else -0.04)
        rows.append(
            Candle(
                timestamp=ts,
                open=price,
                high=max(price, close) + 0.2,
                low=min(price, close) - 0.2,
                close=close,
                volume=1000.0 + i,
            )
        )
        ts += timedelta(days=1)
        price = close
    return tuple(rows)


class CompareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.output_dir = self.tempdir.name
        self.runner = ResearchRunner()
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        self.candles = InlineCandleSource(candles=make_candles())

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _run_strategy(self, run_name: str) -> str:
        artifact = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
                ),
                run_config=ResearchRunConfig(
                    run_name=run_name,
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        return artifact.run_id

    def _run_ml(self, run_name: str) -> str:
        artifact = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.ML_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                ml_spec=MLWorkflowSpec(
                    task_type=TaskType.CLASSIFICATION,
                    label_specs=(
                        FutureReturnLabelSpec(horizon_bars=3, name="ret_h3"),
                        DirectionLabelSpec(horizon_bars=3, threshold=0.0, name="dir_h3"),
                    ),
                    target_label="dir_h3",
                    model_specs=(ModelSpec(model_id="dummy_cls", family=ModelFamily.DUMMY_CLASSIFIER),),
                ),
                run_config=ResearchRunConfig(
                    run_name=run_name,
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        return artifact.run_id

    def test_compare_strategy_runs(self) -> None:
        run_a = self._run_strategy("strategy-a")
        run_b = self._run_strategy("strategy-b")
        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[run_a, run_b],
            mode="strategy",
        )
        self.assertEqual(result.mode, "strategy")
        self.assertEqual(len(result.rows), 2)
        self.assertGreaterEqual(len(result.cards), 1)

    def test_compare_ml_runs(self) -> None:
        run_a = self._run_ml("ml-a")
        run_b = self._run_ml("ml-b")
        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[run_a, run_b],
            mode="ml",
        )
        self.assertEqual(result.mode, "ml")
        self.assertEqual(len(result.rows), 2)
        self.assertGreaterEqual(len(result.cards), 1)

    def test_mixed_compare_rejected(self) -> None:
        run_strategy = self._run_strategy("strategy-only")
        run_ml = self._run_ml("ml-only")
        with self.assertRaises(ValueError):
            compare_saved_runs(
                root_dir=Path(self.output_dir),
                run_ids=[run_strategy, run_ml],
                mode="auto",
            )


if __name__ == "__main__":
    unittest.main()
