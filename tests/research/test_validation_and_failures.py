import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import BacktestConfig  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from ml_data import DirectionLabelSpec, FeatureSpec, FutureReturnLabelSpec, SplitSpec  # noqa: E402
from modeling import ModelFamily, ModelSpec, TaskType, TrainingConfig  # noqa: E402
from research import (  # noqa: E402
    InlineCandleSource,
    MLWorkflowSpec,
    MarketDataFetchSource,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    RunStatus,
    StepStatus,
    StrategyWorkflowSpec,
)


def candles(count: int = 260) -> tuple[Candle, ...]:
    out: list[Candle] = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    px = 100.0
    for _ in range(count):
        close = px + 0.2
        out.append(
            Candle(
                timestamp=ts,
                open=px,
                high=close + 0.2,
                low=px - 0.2,
                close=close,
                volume=1000.0,
            )
        )
        px = close
        ts += timedelta(days=1)
    return tuple(out)


def valid_ml_spec() -> MLWorkflowSpec:
    return MLWorkflowSpec(
        feature_spec=FeatureSpec(),
        label_specs=(
            FutureReturnLabelSpec(horizon_bars=3, name="ret_h3"),
            DirectionLabelSpec(horizon_bars=3, threshold=0.0, name="dir_h3"),
        ),
        split_spec=SplitSpec(0.70, 0.15, 0.15, gap_bars=1),
        task_type=TaskType.CLASSIFICATION,
        target_label="dir_h3",
        model_specs=(ModelSpec(model_id="dummy_cls", family=ModelFamily.DUMMY_CLASSIFIER),),
    )


class ValidationFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        self.candle_data = candles()
        self.runner = ResearchRunner()

    def test_missing_strategy_spec_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.runner.run(
                ResearchRunRequest(
                    workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                    instrument=self.instrument,
                    interval=BarInterval.D1,
                    candle_source=InlineCandleSource(candles=self.candle_data),
                    strategy_spec=None,
                )
            )

    def test_invalid_ml_target_label_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.runner.run(
                ResearchRunRequest(
                    workflow_type=ResearchWorkflowType.ML_RESEARCH,
                    instrument=self.instrument,
                    interval=BarInterval.D1,
                    candle_source=InlineCandleSource(candles=self.candle_data),
                    ml_spec=MLWorkflowSpec(
                        feature_spec=FeatureSpec(),
                        label_specs=(FutureReturnLabelSpec(horizon_bars=2, name="ret_h2"),),
                        task_type=TaskType.CLASSIFICATION,
                        target_label="ret_h2",
                    ),
                )
            )

    def test_market_data_fetch_without_service_fails_cleanly(self) -> None:
        request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
            instrument=self.instrument,
            interval=BarInterval.D1,
            candle_source=MarketDataFetchSource(
                provider_name="oanda",
                start=datetime(2026, 1, 1, tzinfo=timezone.utc),
                end=datetime(2026, 1, 10, tzinfo=timezone.utc),
            ),
            strategy_spec=StrategyWorkflowSpec(
                backtest_config=BacktestConfig(warmup_bars=20, min_signal_confidence=0.10)
            ),
        )
        artifact = self.runner.run(request)
        self.assertEqual(artifact.status, RunStatus.FAILED)
        self.assertEqual(artifact.step_results[0].step_name, "resolve_candles")
        self.assertEqual(artifact.step_results[0].status, StepStatus.FAILED)
        self.assertIn("market_data_service", (artifact.step_results[0].error_message or ""))

    def test_non_strict_hybrid_can_return_partial_failure(self) -> None:
        request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.HYBRID_RESEARCH,
            instrument=self.instrument,
            interval=BarInterval.D1,
            candle_source=InlineCandleSource(candles=self.candle_data),
            strategy_spec=StrategyWorkflowSpec(
                backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.10)
            ),
            ml_spec=MLWorkflowSpec(
                feature_spec=valid_ml_spec().feature_spec,
                label_specs=valid_ml_spec().label_specs,
                split_spec=valid_ml_spec().split_spec,
                task_type=valid_ml_spec().task_type,
                target_label=valid_ml_spec().target_label,
                model_specs=valid_ml_spec().model_specs,
                training_config=TrainingConfig(minimum_train_rows=10_000),
            ),
            run_config=ResearchRunConfig(strict_failures=False),
        )
        artifact = self.runner.run(request)
        self.assertEqual(artifact.status, RunStatus.PARTIAL_FAILURE)
        self.assertIsNotNone(artifact.strategy_output)
        self.assertIsNone(artifact.ml_output)
        self.assertIn("ml_model_training", [s.step_name for s in artifact.step_results])
        failed_steps = [s for s in artifact.step_results if s.status == StepStatus.FAILED]
        self.assertGreaterEqual(len(failed_steps), 1)


if __name__ == "__main__":
    unittest.main()

