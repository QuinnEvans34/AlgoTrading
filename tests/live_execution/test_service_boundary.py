import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from live_execution import (  # noqa: E402
    LiveBrokerName,
    LiveExecutionDisabledError,
    LiveExecutionService,
    LiveExecutionSettings,
    LiveOrderSide,
    LiveOrderType,
    LiveTradeIntent,
)
from live_execution.brokers.registry import create_broker_adapter  # noqa: E402
from market_data import AssetClass, Instrument  # noqa: E402


class LiveExecutionServiceBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intent = LiveTradeIntent(
            instrument=Instrument(symbol="EUR_USD", asset_class=AssetClass.FOREX),
            side=LiveOrderSide.BUY,
            order_type=LiveOrderType.MARKET,
            quantity=1_000.0,
        )

    def test_disabled_by_default_status_and_submit_rejection(self) -> None:
        settings = LiveExecutionSettings()
        service = LiveExecutionService(
            settings=settings,
            adapter=create_broker_adapter(settings),
        )

        status = service.get_status()
        self.assertEqual(status.broker_name, LiveBrokerName.NULL)
        self.assertEqual(status.state.value, "disabled")
        self.assertFalse(status.enabled)
        self.assertFalse(status.configured)

        validation = service.validate_intent(self.intent)
        self.assertFalse(validation.accepted)
        self.assertIn("live_execution_disabled", validation.reasons)
        self.assertIn("broker_not_configured", validation.reasons)

        with self.assertRaises(LiveExecutionDisabledError):
            service.submit_intent(self.intent)

    def test_enabled_but_submission_disabled_ready_status(self) -> None:
        settings = LiveExecutionSettings(
            enabled=True,
            allow_order_submission=False,
            broker_name=LiveBrokerName.OANDA_STUB,
            oanda_api_token="placeholder-token",
            oanda_account_id="placeholder-account",
        )
        service = LiveExecutionService(
            settings=settings,
            adapter=create_broker_adapter(settings),
        )
        status = service.get_status()
        self.assertEqual(status.broker_name, LiveBrokerName.OANDA_STUB)
        self.assertEqual(status.state.value, "ready")
        self.assertFalse(status.submission_allowed)


if __name__ == "__main__":
    unittest.main()

