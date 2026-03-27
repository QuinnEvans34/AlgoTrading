import math
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import AssetClass, BarInterval, Instrument  # noqa: E402
from ml_data.contracts import (  # noqa: E402
    DatasetMetadata,
    MLDatasetArtifact,
    MLDatasetRow,
)
from modeling import (  # noqa: E402
    ModelFamily,
    ModelSpec,
    OptionalDependencyPolicy,
    TaskType,
    TrainingConfig,
    TrainingRequest,
    train_and_evaluate,
)
from modeling.models import OptionalDependencyUnavailableError  # noqa: E402


def make_manual_dataset(*, include_nan: bool = False) -> MLDatasetArtifact:
    instrument = Instrument(symbol="MSFT", asset_class=AssetClass.STOCK)
    ts = datetime(2026, 5, 1, tzinfo=timezone.utc)
    rows: list[MLDatasetRow] = []
    for i in range(40):
        rows.append(
            MLDatasetRow(
                timestamp=ts,
                features={
                    "const_feat": 1.0,
                    "vary_feat": float(i) if not include_nan or i != 5 else math.nan,
                },
                labels={"y_reg": float(i) / 100.0, "y_cls": int(i % 2)},
            )
        )
        ts += timedelta(days=1)

    return MLDatasetArtifact(
        instrument=instrument,
        interval=BarInterval.D1,
        rows=tuple(rows),
        feature_names=("const_feat", "vary_feat"),
        label_names=("y_reg", "y_cls"),
        metadata=DatasetMetadata(
            dataset_id="manual-ds",
            instrument_symbol=instrument.symbol,
            interval=BarInterval.D1,
            feature_names=("const_feat", "vary_feat"),
            label_names=("y_reg", "y_cls"),
            max_feature_lookback_bars=1,
            max_label_horizon_bars=1,
            input_row_count=len(rows),
            output_row_count=len(rows),
            dropped_warmup_rows=0,
            dropped_horizon_rows=0,
            dropped_missing_rows=0,
            start_timestamp=rows[0].timestamp,
            end_timestamp=rows[-1].timestamp,
            signature_sha256="manual-signature",
        ),
        splits=None,
    )


class EdgeCaseTests(unittest.TestCase):
    def test_optional_dependency_skip_policy(self) -> None:
        dataset = make_manual_dataset()
        request = TrainingRequest(
            dataset=dataset,
            target_label="y_reg",
            task_type=TaskType.REGRESSION,
            model_specs=(
                ModelSpec(
                    model_id="lin_sklearn",
                    family=ModelFamily.LINEAR_REGRESSION_SKLEARN,
                    requires_optional_dependency=True,
                ),
            ),
            config=TrainingConfig(
                optional_dependency_policy=OptionalDependencyPolicy.SKIP_UNAVAILABLE_MODELS,
            ),
        )
        run = train_and_evaluate(request)
        self.assertEqual(len(run.model_reports), 1)
        self.assertTrue(run.model_reports[0].skipped)
        self.assertIn("scikit-learn", run.model_reports[0].skip_reason or "")

    def test_optional_dependency_error_policy(self) -> None:
        dataset = make_manual_dataset()
        request = TrainingRequest(
            dataset=dataset,
            target_label="y_reg",
            task_type=TaskType.REGRESSION,
            model_specs=(
                ModelSpec(
                    model_id="lin_sklearn",
                    family=ModelFamily.LINEAR_REGRESSION_SKLEARN,
                    requires_optional_dependency=True,
                ),
            ),
            config=TrainingConfig(
                optional_dependency_policy=OptionalDependencyPolicy.ERROR_ON_UNAVAILABLE_MODELS,
            ),
        )
        with self.assertRaises(OptionalDependencyUnavailableError):
            train_and_evaluate(request)

    def test_zero_variance_feature_is_dropped(self) -> None:
        dataset = make_manual_dataset()
        run = train_and_evaluate(
            TrainingRequest(
                dataset=dataset,
                target_label="y_reg",
                task_type=TaskType.REGRESSION,
                model_specs=(ModelSpec("dummy", ModelFamily.DUMMY_REGRESSOR),),
            )
        )
        dropped = run.run_metadata["dropped_zero_variance_features"]
        self.assertIn("const_feat", dropped)
        self.assertEqual(run.run_metadata["feature_count_used"], 1)

    def test_missing_values_rejected(self) -> None:
        dataset = make_manual_dataset(include_nan=True)
        with self.assertRaises(ValueError):
            train_and_evaluate(
                TrainingRequest(
                    dataset=dataset,
                    target_label="y_reg",
                    task_type=TaskType.REGRESSION,
                    model_specs=(ModelSpec("dummy", ModelFamily.DUMMY_REGRESSOR),),
                )
            )


if __name__ == "__main__":
    unittest.main()

