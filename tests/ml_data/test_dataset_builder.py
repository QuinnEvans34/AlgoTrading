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
    MissingVolumePolicy,
    build_ml_dataset,
)


def make_candles(count: int = 14) -> tuple[Candle, ...]:
    out: list[Candle] = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + 1.0
        out.append(
            Candle(
                timestamp=ts,
                open=price,
                high=close + 0.5,
                low=price - 0.5,
                close=close,
                volume=1000.0 + i * 10.0,
            )
        )
        ts += timedelta(days=1)
        price = close
    return tuple(out)


class DatasetBuilderTests(unittest.TestCase):
    def test_build_dataset_and_metadata(self) -> None:
        instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        candles = make_candles()

        request = MLDatasetRequest(
            instrument=instrument,
            interval=BarInterval.D1,
            candles=candles,
            feature_spec=FeatureSpec(
                return_windows=(1, 2),
                log_return_windows=(1,),
                volatility_windows=(3,),
                momentum_windows=(2,),
                sma_windows=(3,),
                sma_crossover_pairs=((2, 3),),
                atr_windows=(3,),
                zscore_windows=(3,),
                include_candle_structure=True,
                include_volume_features=True,
                volume_zscore_windows=(3,),
            ),
            label_specs=(
                FutureReturnLabelSpec(horizon_bars=2, name="target_ret_2"),
                DirectionLabelSpec(horizon_bars=2, threshold=0.0, name="target_dir_2"),
            ),
            missing_volume_policy=MissingVolumePolicy.REQUIRE_VOLUME,
        )

        dataset = build_ml_dataset(request)
        self.assertEqual(dataset.instrument.symbol, "AAPL")
        self.assertGreater(len(dataset.feature_names), 0)
        self.assertEqual(dataset.label_names, ("target_ret_2", "target_dir_2"))
        self.assertEqual(dataset.metadata.max_feature_lookback_bars, 3)
        self.assertEqual(dataset.metadata.max_label_horizon_bars, 2)
        self.assertEqual(dataset.metadata.dropped_warmup_rows, 3)
        self.assertEqual(dataset.metadata.dropped_horizon_rows, 2)
        self.assertEqual(dataset.metadata.dropped_missing_rows, 0)
        self.assertEqual(len(dataset.rows), len(candles) - 3 - 2)

        first_row = dataset.rows[0]
        self.assertAlmostEqual(first_row.features["return_1"], 1.0 / 103.0, places=12)
        self.assertIn("candle_body_ratio", first_row.features)
        self.assertIn("volume_change_1", first_row.features)
        self.assertIn("target_ret_2", first_row.labels)
        self.assertIn("target_dir_2", first_row.labels)
        self.assertIn("signature_sha256", dataset.metadata.__dict__)


if __name__ == "__main__":
    unittest.main()

