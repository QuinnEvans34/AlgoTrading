"""Minimal demo: normalized candles -> ML feature/label dataset artifact."""

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


def synthetic_candles(count: int = 260) -> tuple[Candle, ...]:
    random.seed(42)
    out: list[Candle] = []
    ts = datetime.now(timezone.utc) - timedelta(days=count)
    price = 100.0
    for i in range(count):
        drift = 0.08 if i < int(count * 0.55) else -0.04
        wave = math.sin(i / 9.0) * 0.6
        shock = random.uniform(-0.7, 0.7)
        close = max(1.0, price + drift + wave + shock)
        high = max(price, close) + random.uniform(0.01, 0.35)
        low = min(price, close) - random.uniform(0.01, 0.35)
        volume = 1_000_000.0 + random.uniform(-150_000.0, 180_000.0)
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
    candles = synthetic_candles()
    instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)

    request = MLDatasetRequest(
        instrument=instrument,
        interval=BarInterval.D1,
        candles=candles,
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

    dataset = build_ml_dataset(request)
    print("ML Dataset Summary")
    print("------------------")
    print(f"Dataset id: {dataset.metadata.dataset_id}")
    print(f"Rows: {len(dataset.rows)}")
    print(f"Features: {len(dataset.feature_names)}")
    print(f"Labels: {dataset.label_names}")
    print(f"Lookback bars: {dataset.metadata.max_feature_lookback_bars}")
    print(f"Horizon bars: {dataset.metadata.max_label_horizon_bars}")
    print(f"Dropped rows (warmup/horizon/missing): "
          f"{dataset.metadata.dropped_warmup_rows}/"
          f"{dataset.metadata.dropped_horizon_rows}/"
          f"{dataset.metadata.dropped_missing_rows}")

    if dataset.splits is not None:
        print()
        print("Splits")
        print("------")
        print(f"Train rows: {len(dataset.splits.train.rows)}")
        print(f"Validation rows: {len(dataset.splits.validation.rows)}")
        print(f"Test rows: {len(dataset.splits.test.rows)}")
        print(f"Gap rows dropped: {len(dataset.splits.dropped_gap_indices)}")

    if dataset.rows:
        first = dataset.rows[0]
        print()
        print("First Row Snapshot")
        print("------------------")
        print(f"Timestamp: {first.timestamp.isoformat()}")
        print(f"Feature names (first 8): {dataset.feature_names[:8]}")
        print(f"Feature sample (first 5): {list(first.features.items())[:5]}")
        print(f"Labels: {first.labels}")


if __name__ == "__main__":
    main()

