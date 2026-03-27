import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from live_execution import (  # noqa: E402
    BrokerCapabilities,
    LiveOrderSide,
    LiveOrderType,
    LiveTradeIntent,
)
from live_execution.validation import validate_intent_against_capabilities  # noqa: E402
from market_data import AssetClass, Instrument  # noqa: E402


class LiveIntentValidationTests(unittest.TestCase):
    def test_unsupported_order_type_and_short_restriction(self) -> None:
        capabilities = BrokerCapabilities(
            supported_asset_classes=(AssetClass.FOREX,),
            supported_order_types=(LiveOrderType.MARKET,),
            supported_order_sides=(LiveOrderSide.BUY, LiveOrderSide.SELL),
            supports_short=False,
            supports_cancel=False,
            supports_submit=False,
        )
        intent = LiveTradeIntent(
            instrument=Instrument(symbol="EUR_USD", asset_class=AssetClass.FOREX),
            side=LiveOrderSide.SELL,
            order_type=LiveOrderType.LIMIT,
            quantity=10_000.0,
            limit_price=1.10,
        )
        reasons = validate_intent_against_capabilities(intent, capabilities)
        self.assertIn("unsupported_order_type:limit", reasons)
        self.assertIn("short_or_sell_not_supported", reasons)

    def test_limit_requires_positive_price(self) -> None:
        capabilities = BrokerCapabilities(
            supported_asset_classes=(AssetClass.FOREX,),
            supported_order_types=(LiveOrderType.LIMIT,),
            supported_order_sides=(LiveOrderSide.BUY,),
            supports_short=True,
            supports_cancel=True,
            supports_submit=False,
        )
        intent = LiveTradeIntent(
            instrument=Instrument(symbol="EUR_USD", asset_class=AssetClass.FOREX),
            side=LiveOrderSide.BUY,
            order_type=LiveOrderType.LIMIT,
            quantity=2_000.0,
            limit_price=None,
        )
        reasons = validate_intent_against_capabilities(intent, capabilities)
        self.assertIn("limit_price_must_be_greater_than_zero", reasons)
        self.assertIn("limit_price_required", reasons)


if __name__ == "__main__":
    unittest.main()

