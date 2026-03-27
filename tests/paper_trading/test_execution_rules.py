import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import AssetClass, Instrument  # noqa: E402
from paper_trading import (  # noqa: E402
    PaperAccountConfig,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
)
from paper_trading.execution import (  # noqa: E402
    compute_limit_fill,
    compute_market_fill,
    is_limit_marketable,
)


class ExecutionRulesTests(unittest.TestCase):
    def test_market_fill_applies_friction_and_commission(self) -> None:
        order = PaperOrder(
            order_id="paper-order-00000001",
            instrument=Instrument(symbol="AAPL", asset_class=AssetClass.STOCK),
            side=PaperOrderSide.BUY,
            order_type=PaperOrderType.MARKET,
            quantity=10.0,
            status=PaperOrderStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        config = PaperAccountConfig(
            default_spread_bps=2.0,
            default_slippage_bps=1.0,
            commission_bps=5.0,
            commission_fixed=0.25,
        )
        fill = compute_market_fill(order=order, base_price=100.0, config=config)
        self.assertGreater(fill.fill_price, 100.0)
        self.assertGreater(fill.spread_cost, 0.0)
        self.assertGreater(fill.slippage_cost, 0.0)
        self.assertGreater(fill.commission, 0.0)

    def test_limit_marketable_rules(self) -> None:
        buy_limit = PaperOrder(
            order_id="paper-order-1",
            instrument=Instrument(symbol="AAPL", asset_class=AssetClass.STOCK),
            side=PaperOrderSide.BUY,
            order_type=PaperOrderType.LIMIT,
            quantity=5.0,
            status=PaperOrderStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            limit_price=99.0,
        )
        sell_limit = PaperOrder(
            order_id="paper-order-2",
            instrument=Instrument(symbol="AAPL", asset_class=AssetClass.STOCK),
            side=PaperOrderSide.SELL,
            order_type=PaperOrderType.LIMIT,
            quantity=5.0,
            status=PaperOrderStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            limit_price=101.0,
        )
        self.assertTrue(is_limit_marketable(buy_limit, 98.5))
        self.assertFalse(is_limit_marketable(buy_limit, 99.5))
        self.assertTrue(is_limit_marketable(sell_limit, 101.5))
        self.assertFalse(is_limit_marketable(sell_limit, 100.5))

    def test_limit_fill_uses_limit_price(self) -> None:
        order = PaperOrder(
            order_id="paper-order-3",
            instrument=Instrument(symbol="EURUSD", asset_class=AssetClass.FOREX),
            side=PaperOrderSide.SELL,
            order_type=PaperOrderType.LIMIT,
            quantity=10_000.0,
            status=PaperOrderStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            limit_price=1.1030,
        )
        config = PaperAccountConfig(commission_bps=0.0, commission_fixed=0.0)
        fill = compute_limit_fill(order=order, config=config)
        self.assertEqual(fill.fill_price, 1.1030)
        self.assertEqual(fill.spread_cost, 0.0)
        self.assertEqual(fill.slippage_cost, 0.0)


if __name__ == "__main__":
    unittest.main()

