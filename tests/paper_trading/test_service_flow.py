import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import AssetClass, Instrument  # noqa: E402
from paper_trading import (  # noqa: E402
    PaperAccountConfig,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderType,
    PaperTradingService,
    PaperTradingStorage,
    PriceUpdate,
)


class PaperTradingServiceFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        storage = PaperTradingStorage(Path(self.tempdir.name))
        config = PaperAccountConfig(
            initial_cash=100_000.0,
            allow_short=False,
            default_spread_bps=0.0,
            default_slippage_bps=0.0,
            commission_bps=0.0,
            commission_fixed=0.0,
        )
        self.service = PaperTradingService(storage=storage, default_config=config)
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_market_then_limit_flow(self) -> None:
        entry = self.service.place_order(
            PaperOrderRequest(
                instrument=self.instrument,
                side=PaperOrderSide.BUY,
                order_type=PaperOrderType.MARKET,
                quantity=10.0,
                reference_price=100.0,
            )
        )
        self.assertEqual(entry.order.status.value, "filled")
        self.assertEqual(len(entry.fills), 1)
        self.assertEqual(len(entry.state.positions), 1)
        self.assertAlmostEqual(entry.state.positions[0].quantity, 10.0)

        limit = self.service.place_order(
            PaperOrderRequest(
                instrument=self.instrument,
                side=PaperOrderSide.SELL,
                order_type=PaperOrderType.LIMIT,
                quantity=10.0,
                limit_price=110.0,
            )
        )
        self.assertEqual(limit.order.status.value, "open")
        self.assertEqual(len(limit.state.open_orders), 1)

        no_fill = self.service.process_price_update(
            PriceUpdate(
                instrument=self.instrument,
                price=109.0,
                timestamp=datetime.now(timezone.utc),
            )
        )
        self.assertEqual(len(no_fill.filled_order_ids), 0)
        self.assertEqual(len(no_fill.state.open_orders), 1)

        filled = self.service.process_price_update(
            PriceUpdate(
                instrument=self.instrument,
                price=110.0,
                timestamp=datetime.now(timezone.utc),
            )
        )
        self.assertEqual(len(filled.filled_order_ids), 1)
        self.assertEqual(len(filled.state.open_orders), 0)
        self.assertEqual(len(filled.state.positions), 0)
        self.assertGreater(filled.state.account.realized_pnl, 0.0)

    def test_short_disabled_rejects_short_sell(self) -> None:
        with self.assertRaises(ValueError):
            self.service.place_order(
                PaperOrderRequest(
                    instrument=self.instrument,
                    side=PaperOrderSide.SELL,
                    order_type=PaperOrderType.MARKET,
                    quantity=1.0,
                    reference_price=100.0,
                )
            )


if __name__ == "__main__":
    unittest.main()

