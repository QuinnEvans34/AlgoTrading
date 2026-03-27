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
    FeatureSpec,
    FutureReturnLabelSpec,
    MLDatasetRequest,
    SplitSpec,
    build_ml_dataset,
)


def make_candles(count: int = 30) -> tuple[Candle, ...]:
    out: list[Candle] = []
    ts = datetime(2026, 3, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + 0.4
        out.append(
            Candle(
                timestamp=ts,
                open=price,
                high=close + 0.2,
                low=price - 0.2,
                close=close,
                volume=10000.0 + i,
            )
        )
        ts += timedelta(days=1)
        price = close
    return tuple(out)


class SplitTests(unittest.TestCase):
    def test_chronological_splits_with_gap(self) -> None:
        instrument = Instrument(symbol="EUR_USD", asset_class=AssetClass.FOREX)
        dataset = build_ml_dataset(
            MLDatasetRequest(
                instrument=instrument,
                interval=BarInterval.D1,
                candles=make_candles(),
                feature_spec=FeatureSpec(
                    return_windows=(1,),
                    log_return_windows=(1,),
                    volatility_windows=(3,),
                    momentum_windows=(2,),
                    sma_windows=(3,),
                    sma_crossover_pairs=((2, 3),),
                    atr_windows=(3,),
                    zscore_windows=(3,),
                    include_volume_features=False,
                ),
                label_specs=(FutureReturnLabelSpec(horizon_bars=1, name="fwd1"),),
                split_spec=SplitSpec(
                    train_fraction=0.60,
                    validation_fraction=0.20,
                    test_fraction=0.20,
                    gap_bars=1,
                ),
            )
        )

        self.assertIsNotNone(dataset.splits)
        assert dataset.splits is not None

        train = dataset.splits.train.indices
        validation = dataset.splits.validation.indices
        test = dataset.splits.test.indices

        self.assertGreater(len(train), 0)
        self.assertGreater(len(validation), 0)
        self.assertGreater(len(test), 0)

        self.assertTrue(set(train).isdisjoint(validation))
        self.assertTrue(set(train).isdisjoint(test))
        self.assertTrue(set(validation).isdisjoint(test))

        all_used = set(train) | set(validation) | set(test)
        self.assertEqual(max(all_used), len(dataset.rows) - 1)
        self.assertEqual(min(all_used), 0)
        self.assertEqual(len(dataset.splits.dropped_gap_indices), 2)


if __name__ == "__main__":
    unittest.main()

