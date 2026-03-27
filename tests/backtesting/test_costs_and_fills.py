import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import (  # noqa: E402
    CompositeCommissionModel,
    FillModel,
    FixedBpsCommissionModel,
    FixedBpsSlippageModel,
    FixedBpsSpreadModel,
    FixedFeeCommissionModel,
    PositionDirection,
)
from market_data import AssetClass, Instrument  # noqa: E402


class CostAndFillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        self.timestamp = datetime.now(timezone.utc)

    def test_fill_model_direction_and_friction(self) -> None:
        fill_model = FillModel(
            spread_model=FixedBpsSpreadModel(half_spread_bps=1.0),
            slippage_model=FixedBpsSlippageModel(bps=2.0),
        )
        raw = 100.0
        # Total friction = 3 bps = 0.0003
        self.assertAlmostEqual(
            fill_model.entry_fill_price(
                instrument=self.instrument,
                timestamp=self.timestamp,
                raw_price=raw,
                direction=PositionDirection.LONG,
            ),
            100.03,
            places=6,
        )
        self.assertAlmostEqual(
            fill_model.exit_fill_price(
                instrument=self.instrument,
                timestamp=self.timestamp,
                raw_price=raw,
                direction=PositionDirection.LONG,
            ),
            99.97,
            places=6,
        )
        self.assertAlmostEqual(
            fill_model.entry_fill_price(
                instrument=self.instrument,
                timestamp=self.timestamp,
                raw_price=raw,
                direction=PositionDirection.SHORT,
            ),
            99.97,
            places=6,
        )
        self.assertAlmostEqual(
            fill_model.exit_fill_price(
                instrument=self.instrument,
                timestamp=self.timestamp,
                raw_price=raw,
                direction=PositionDirection.SHORT,
            ),
            100.03,
            places=6,
        )

    def test_commission_models(self) -> None:
        notional = 10_000.0
        bps = FixedBpsCommissionModel(bps=2.0)
        fixed = FixedFeeCommissionModel(fee_per_fill=1.25)
        combo = CompositeCommissionModel(notional_bps=1.0, fixed_fee=0.50)

        self.assertAlmostEqual(
            bps.commission(
                instrument=self.instrument,
                timestamp=self.timestamp,
                notional=notional,
            ),
            2.0,
            places=6,
        )
        self.assertAlmostEqual(
            fixed.commission(
                instrument=self.instrument,
                timestamp=self.timestamp,
                notional=notional,
            ),
            1.25,
            places=6,
        )
        self.assertAlmostEqual(
            combo.commission(
                instrument=self.instrument,
                timestamp=self.timestamp,
                notional=notional,
            ),
            1.50,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
