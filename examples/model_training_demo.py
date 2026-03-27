"""Minimal demo: ML dataset artifact -> baseline model training/evaluation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from ml_data import (  # noqa: E402
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    MLDatasetRequest,
    MissingVolumePolicy,
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


def synthetic_candles(count: int = 320) -> tuple[Candle, ...]:
    random.seed(7)
    out: list[Candle] = []
    ts = datetime.now(timezone.utc) - timedelta(days=count)
    price = 100.0
    for i in range(count):
        drift = 0.08 if i < int(count * 0.6) else -0.03
        wave = math.sin(i / 12.0) * 0.7
        shock = random.uniform(-0.5, 0.5)
        close = max(1.0, price + drift + wave + shock)
        high = max(price, close) + random.uniform(0.01, 0.25)
        low = min(price, close) - random.uniform(0.01, 0.25)
        volume = 2_000_000.0 + random.uniform(-250_000.0, 220_000.0)
        out.append(
            Candle(
                timestamp=ts,
                open=price,
                high=high,
                low=low,
                close=close,
                volume=max(1.0, volume),
            )
        )
        price = close
        ts += timedelta(days=1)
    return tuple(out)


def main() -> None:
    instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
    dataset = build_ml_dataset(
        MLDatasetRequest(
            instrument=instrument,
            interval=BarInterval.D1,
            candles=synthetic_candles(),
            feature_spec=FeatureSpec(
                return_windows=(1, 5, 10),
                log_return_windows=(1, 5),
                volatility_windows=(5, 20),
                momentum_windows=(3, 10),
                sma_windows=(10, 20),
                sma_crossover_pairs=((5, 20),),
                atr_windows=(14,),
                zscore_windows=(20,),
                include_candle_structure=True,
                include_volume_features=True,
                volume_zscore_windows=(10,),
            ),
            label_specs=(
                FutureReturnLabelSpec(horizon_bars=5, name="target_return_5"),
                DirectionLabelSpec(horizon_bars=5, threshold=0.0, name="target_direction_5"),
            ),
            split_spec=SplitSpec(train_fraction=0.70, validation_fraction=0.15, test_fraction=0.15, gap_bars=2),
            missing_volume_policy=MissingVolumePolicy.REQUIRE_VOLUME,
        )
    )

    regression_run = train_and_evaluate(
        TrainingRequest(
            dataset=dataset,
            target_label="target_return_5",
            task_type=TaskType.REGRESSION,
            model_specs=(
                ModelSpec(model_id="dummy_reg", family=ModelFamily.DUMMY_REGRESSOR),
                ModelSpec(
                    model_id="ridge_np",
                    family=ModelFamily.RIDGE_REGRESSOR_NUMPY,
                    hyperparameters={"alpha": 1.0},
                ),
            ),
        )
    )

    classification_run = train_and_evaluate(
        TrainingRequest(
            dataset=dataset,
            target_label="target_direction_5",
            task_type=TaskType.CLASSIFICATION,
            model_specs=(
                ModelSpec(model_id="dummy_cls", family=ModelFamily.DUMMY_CLASSIFIER),
            ),
        )
    )

    print("Regression Run")
    print("--------------")
    for row in regression_run.comparison_table:
        print(
            f"{row.model_id}: {row.primary_metric_name} "
            f"(val={row.validation_value}, test={row.test_value})"
        )
    for report in regression_run.model_reports:
        if report.feature_importance:
            print("Top feature importance:", report.feature_importance[:5])
            break

    print()
    print("Classification Run")
    print("------------------")
    for row in classification_run.comparison_table:
        print(
            f"{row.model_id}: {row.primary_metric_name} "
            f"(val={row.validation_value}, test={row.test_value})"
        )
    report = classification_run.model_reports[0]
    if "test" in report.metrics_by_split:
        print("Test metrics:", report.metrics_by_split["test"])


if __name__ == "__main__":
    main()

