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
    build_ml_dataset,
)


def candles_from_closes(closes: list[float]) -> tuple[Candle, ...]:
    out: list[Candle] = []
    ts = datetime(2026, 2, 1, tzinfo=timezone.utc)
    prev = closes[0] - 1.0
    for close in closes:
        out.append(
            Candle(
                timestamp=ts,
                open=prev,
                high=max(prev, close) + 0.2,
                low=min(prev, close) - 0.2,
                close=close,
                volume=5000.0,
            )
        )
        ts += timedelta(days=1)
        prev = close
    return tuple(out)


class LeakageGuardTests(unittest.TestCase):
    def test_historical_features_not_affected_by_future_mutation(self) -> None:
        instrument = Instrument(symbol="SPY", asset_class=AssetClass.STOCK)
        base_closes = [100, 101, 102, 103, 104, 105, 106, 107]
        changed_closes = [100, 101, 102, 103, 104, 105, 106, 1000]

        request_base = MLDatasetRequest(
            instrument=instrument,
            interval=BarInterval.D1,
            candles=candles_from_closes(base_closes),
            feature_spec=FeatureSpec(
                return_windows=(1, 2),
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
        )
        request_changed = MLDatasetRequest(
            instrument=instrument,
            interval=BarInterval.D1,
            candles=candles_from_closes(changed_closes),
            feature_spec=request_base.feature_spec,
            label_specs=request_base.label_specs,
        )

        dataset_base = build_ml_dataset(request_base)
        dataset_changed = build_ml_dataset(request_changed)

        row_base = dataset_base.rows[1]  # maps to an early timestamp, far from mutated tail.
        row_changed = dataset_changed.rows[1]
        self.assertEqual(row_base.timestamp, row_changed.timestamp)
        self.assertEqual(row_base.features, row_changed.features)

        # Tail-adjacent labels should differ when a future close changes sharply.
        self.assertNotEqual(dataset_base.rows[-1].labels["fwd1"], dataset_changed.rows[-1].labels["fwd1"])

    def test_warmup_and_horizon_alignment(self) -> None:
        instrument = Instrument(symbol="QQQ", asset_class=AssetClass.STOCK)
        closes = [100, 101, 102, 103, 104, 105, 106, 107]
        dataset = build_ml_dataset(
            MLDatasetRequest(
                instrument=instrument,
                interval=BarInterval.D1,
                candles=candles_from_closes(closes),
                feature_spec=FeatureSpec(
                    return_windows=(1, 2, 3),
                    log_return_windows=(1,),
                    volatility_windows=(3,),
                    momentum_windows=(3,),
                    sma_windows=(3,),
                    sma_crossover_pairs=((2, 3),),
                    atr_windows=(3,),
                    zscore_windows=(3,),
                    include_volume_features=False,
                ),
                label_specs=(FutureReturnLabelSpec(horizon_bars=2, name="fwd2"),),
            )
        )

        # n=8, max lookback=3, horizon=2 -> rows at indices [3,4,5].
        self.assertEqual(len(dataset.rows), 3)
        self.assertEqual(dataset.rows[0].timestamp, candles_from_closes(closes)[3].timestamp)
        self.assertEqual(dataset.rows[-1].timestamp, candles_from_closes(closes)[5].timestamp)


if __name__ == "__main__":
    unittest.main()

