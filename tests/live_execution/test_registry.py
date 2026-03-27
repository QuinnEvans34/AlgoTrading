import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from live_execution import LiveBrokerName, LiveExecutionSettings  # noqa: E402
from live_execution.brokers.null_broker import NullBrokerAdapter  # noqa: E402
from live_execution.brokers.oanda_stub import OandaStubBrokerAdapter  # noqa: E402
from live_execution.brokers.registry import (  # noqa: E402
    create_broker_adapter,
    resolve_broker_name,
)


class LiveBrokerRegistryTests(unittest.TestCase):
    def test_resolve_unknown_broker_falls_back_to_null(self) -> None:
        self.assertEqual(resolve_broker_name("not-a-broker"), LiveBrokerName.NULL)

    def test_null_adapter_resolution(self) -> None:
        adapter = create_broker_adapter(
            LiveExecutionSettings(broker_name=LiveBrokerName.NULL)
        )
        self.assertIsInstance(adapter, NullBrokerAdapter)

    def test_oanda_stub_resolution(self) -> None:
        adapter = create_broker_adapter(
            LiveExecutionSettings(
                broker_name=LiveBrokerName.OANDA_STUB,
                oanda_api_token="token",
                oanda_account_id="acct",
            )
        )
        self.assertIsInstance(adapter, OandaStubBrokerAdapter)
        self.assertTrue(adapter.is_configured())

    def test_oanda_stub_not_configured_without_credentials(self) -> None:
        adapter = create_broker_adapter(
            LiveExecutionSettings(broker_name=LiveBrokerName.OANDA_STUB)
        )
        self.assertIsInstance(adapter, OandaStubBrokerAdapter)
        self.assertFalse(adapter.is_configured())


if __name__ == "__main__":
    unittest.main()

