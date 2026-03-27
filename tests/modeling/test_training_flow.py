import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from ml_data import (  # noqa: E402
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    MLDatasetRequest,
    SplitSpec,
    build_ml_dataset,
)
from modeling import (  # noqa: E402
    ModelFamily,
    ModelSpec,
    TaskType,
    TrainingRequest,
    train_and_evaluate,
)


def build_dataset() -> object:
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []
    price = 100.0
    for i in range(280):
        drift = 0.06 if i < 180 else -0.03
        wave = ((i % 9) - 4) * 0.05
        close = max(1.0, price + drift + wave)
        candles.append(
            Candle(
                timestamp=ts,
                open=price,
                high=max(price, close) + 0.25,
                low=min(price, close) - 0.25,
                close=close,
                volume=5000.0 + i * 2.0,
            )
        )
        price = close
        ts += timedelta(days=1)

    return build_ml_dataset(
        MLDatasetRequest(
            instrument=Instrument(symbol="AAPL", asset_class=AssetClass.STOCK),
            interval=BarInterval.D1,
            candles=tuple(candles),
            feature_spec=FeatureSpec(
                return_windows=(1, 3, 5),
                log_return_windows=(1, 3),
                volatility_windows=(5,),
                momentum_windows=(3, 8),
                sma_windows=(5, 10),
                sma_crossover_pairs=((5, 10),),
                atr_windows=(5,),
                zscore_windows=(10,),
                include_volume_features=False,
            ),
            label_specs=(
                FutureReturnLabelSpec(horizon_bars=3, name="ret_h3"),
                DirectionLabelSpec(horizon_bars=3, threshold=0.0, name="dir_h3"),
            ),
            split_spec=SplitSpec(0.70, 0.15, 0.15, gap_bars=1),
        )
    )


class TrainingFlowTests(unittest.TestCase):
    def test_regression_training_deterministic(self) -> None:
        dataset = build_dataset()
        request = TrainingRequest(
            dataset=dataset,
            target_label="ret_h3",
            task_type=TaskType.REGRESSION,
            model_specs=(
                ModelSpec("dummy_reg", ModelFamily.DUMMY_REGRESSOR),
                ModelSpec("ridge_np", ModelFamily.RIDGE_REGRESSOR_NUMPY, {"alpha": 1.0}),
            ),
        )
        run_a = train_and_evaluate(request)
        run_b = train_and_evaluate(request)

        self.assertEqual(len(run_a.model_reports), 2)
        self.assertEqual(len(run_a.comparison_table), 2)
        self.assertEqual(run_a.comparison_table, run_b.comparison_table)
        self.assertEqual(
            run_a.model_reports[1].predictions_by_split["test"].y_pred,
            run_b.model_reports[1].predictions_by_split["test"].y_pred,
        )

    def test_classification_training(self) -> None:
        dataset = build_dataset()
        request = TrainingRequest(
            dataset=dataset,
            target_label="dir_h3",
            task_type=TaskType.CLASSIFICATION,
            model_specs=(ModelSpec("dummy_cls", ModelFamily.DUMMY_CLASSIFIER),),
        )
        run = train_and_evaluate(request)
        self.assertEqual(len(run.model_reports), 1)
        report = run.model_reports[0]
        self.assertFalse(report.skipped)
        self.assertIn("validation", report.metrics_by_split)
        self.assertIn("test", report.metrics_by_split)
        metric = report.metrics_by_split["test"]
        self.assertGreaterEqual(metric.accuracy, 0.0)
        self.assertLessEqual(metric.accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()

