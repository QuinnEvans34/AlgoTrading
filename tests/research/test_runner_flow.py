import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
import math
import random

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import BacktestConfig  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from ml_data import DirectionLabelSpec, FeatureSpec, FutureReturnLabelSpec, SplitSpec  # noqa: E402
from modeling import ModelFamily, ModelSpec, TaskType  # noqa: E402
from research import (  # noqa: E402
    InlineCandleSource,
    MLWorkflowSpec,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    RunStatus,
    StrategyWorkflowSpec,
)


def make_candles(count: int = 420) -> tuple[Candle, ...]:
    random.seed(5)
    candles: list[Candle] = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        drift = 0.08 if i < 240 else -0.03
        wave = math.sin(i / 15.0) * 0.6
        noise = random.uniform(-0.30, 0.30)
        close = max(1.0, price + drift + wave + noise)
        candles.append(
            Candle(
                timestamp=ts,
                open=price,
                high=max(price, close) + 0.2,
                low=min(price, close) - 0.2,
                close=close,
                volume=1_500_000 + i * 100.0,
            )
        )
        price = close
        ts += timedelta(days=1)
    return tuple(candles)


def ml_spec() -> MLWorkflowSpec:
    return MLWorkflowSpec(
        feature_spec=FeatureSpec(
            return_windows=(1, 3, 5),
            log_return_windows=(1, 3),
            volatility_windows=(5, 20),
            momentum_windows=(3, 10),
            sma_windows=(10, 20),
            sma_crossover_pairs=((10, 20),),
            atr_windows=(14,),
            zscore_windows=(20,),
            include_volume_features=True,
        ),
        label_specs=(
            FutureReturnLabelSpec(horizon_bars=5, name="ret_h5"),
            DirectionLabelSpec(horizon_bars=5, threshold=0.0, name="dir_h5"),
        ),
        split_spec=SplitSpec(0.70, 0.15, 0.15, gap_bars=1),
        task_type=TaskType.CLASSIFICATION,
        target_label="dir_h5",
        model_specs=(ModelSpec(model_id="dummy_cls", family=ModelFamily.DUMMY_CLASSIFIER),),
    )


class RunnerFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        self.candles = make_candles()
        self.runner = ResearchRunner()

    def test_strategy_workflow_runs(self) -> None:
        artifact = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=InlineCandleSource(candles=self.candles),
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=80, min_signal_confidence=0.10)
                ),
            )
        )
        self.assertEqual(artifact.status, RunStatus.SUCCESS)
        self.assertIsNotNone(artifact.strategy_output)
        self.assertIsNone(artifact.ml_output)
        step_names = [step.step_name for step in artifact.step_results]
        self.assertEqual(step_names, ["resolve_candles", "strategy_backtest", "strategy_diagnostics"])

    def test_ml_workflow_runs(self) -> None:
        artifact = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.ML_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=InlineCandleSource(candles=self.candles),
                ml_spec=ml_spec(),
            )
        )
        self.assertEqual(artifact.status, RunStatus.SUCCESS)
        self.assertIsNone(artifact.strategy_output)
        self.assertIsNotNone(artifact.ml_output)
        self.assertEqual(
            [step.step_name for step in artifact.step_results],
            ["resolve_candles", "ml_dataset_build", "ml_model_training"],
        )

    def test_hybrid_workflow_runs(self) -> None:
        artifact = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.HYBRID_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=InlineCandleSource(candles=self.candles),
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=80, min_signal_confidence=0.10)
                ),
                ml_spec=ml_spec(),
            )
        )
        self.assertEqual(artifact.status, RunStatus.SUCCESS)
        self.assertIsNotNone(artifact.strategy_output)
        self.assertIsNotNone(artifact.ml_output)


if __name__ == "__main__":
    unittest.main()

