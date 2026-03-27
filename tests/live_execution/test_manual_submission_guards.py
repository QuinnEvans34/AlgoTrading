import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from live_execution import (  # noqa: E402
    BrokerCapabilities,
    LiveBrokerName,
    LiveExecutionSettings,
    LiveExecutionService,
    LiveOrderSide,
    LiveOrderType,
    LiveTradeIntent,
    ManualLiveOrderRequest,
)
from live_execution.brokers.base import LiveBrokerAdapter  # noqa: E402
from live_execution.brokers.registry import create_broker_adapter  # noqa: E402
from live_execution.contracts import LiveSubmitResult  # noqa: E402
from market_data import AssetClass, Instrument  # noqa: E402


class SubmitCapableFakeAdapter(LiveBrokerAdapter):
    @property
    def broker_name(self) -> LiveBrokerName:
        return LiveBrokerName.OANDA_STUB

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supported_asset_classes=(AssetClass.FOREX,),
            supported_order_types=(LiveOrderType.MARKET, LiveOrderType.LIMIT),
            supported_order_sides=(LiveOrderSide.BUY, LiveOrderSide.SELL),
            supports_short=True,
            supports_cancel=True,
            supports_submit=True,
        )

    def is_configured(self) -> bool:
        return True

    def configuration_message(self) -> str:
        return "configured"

    def map_intent_to_payload(self, intent: LiveTradeIntent):  # noqa: ANN001
        return {
            "instrument": intent.instrument.symbol,
            "side": intent.side.value,
            "type": intent.order_type.value,
            "qty": intent.quantity,
        }

    def submit_intent(self, intent: LiveTradeIntent) -> LiveSubmitResult:
        return LiveSubmitResult(
            accepted=False,
            status="rejected",
            reason="stub_submit_blocked",
            external_order_id=None,
            broker_payload=self.map_intent_to_payload(intent),
        )


class ManualLiveSubmissionGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.attempt_log_path = Path(self.tempdir.name) / "attempts.jsonl"
        self.intent = LiveTradeIntent(
            instrument=Instrument(symbol="EUR_USD", asset_class=AssetClass.FOREX),
            side=LiveOrderSide.BUY,
            order_type=LiveOrderType.MARKET,
            quantity=1_000.0,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _request(self, *, idempotency_key: str = "idem-1", confirmed: bool = True):
        return ManualLiveOrderRequest(
            intent=self.intent,
            idempotency_key=idempotency_key,
            confirm_live_execution=confirmed,
            confirmation_text="EXECUTE LIVE ORDER",
            operator_id="tester",
            operator_note="manual test",
        )

    def test_disabled_by_default_rejection(self) -> None:
        settings = LiveExecutionSettings(
            enabled=False,
            allow_order_submission=False,
            submit_feature_enabled=True,
            status_feature_enabled=True,
            attempt_log_path=str(self.attempt_log_path),
        )
        service = LiveExecutionService(
            settings=settings,
            adapter=create_broker_adapter(settings),
        )
        result = service.submit_manual_order(self._request())
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, "live_execution_disabled")

    def test_missing_confirmation_rejection(self) -> None:
        settings = LiveExecutionSettings(
            enabled=True,
            allow_order_submission=True,
            submit_feature_enabled=True,
            status_feature_enabled=True,
            attempt_log_path=str(self.attempt_log_path),
        )
        service = LiveExecutionService(settings=settings, adapter=SubmitCapableFakeAdapter())
        result = service.submit_manual_order(self._request(confirmed=False))
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, "manual_confirmation_required")

    def test_missing_broker_configuration_rejection(self) -> None:
        settings = LiveExecutionSettings(
            enabled=True,
            allow_order_submission=True,
            submit_feature_enabled=True,
            status_feature_enabled=True,
            broker_name=LiveBrokerName.OANDA_STUB,
            attempt_log_path=str(self.attempt_log_path),
        )
        service = LiveExecutionService(
            settings=settings,
            adapter=create_broker_adapter(settings),
        )
        result = service.submit_manual_order(self._request())
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, "broker_not_configured")

    def test_unsupported_submit_capability_rejection(self) -> None:
        settings = LiveExecutionSettings(
            enabled=True,
            allow_order_submission=True,
            submit_feature_enabled=True,
            status_feature_enabled=True,
            broker_name=LiveBrokerName.OANDA_STUB,
            oanda_api_token="token",
            oanda_account_id="acct",
            attempt_log_path=str(self.attempt_log_path),
        )
        service = LiveExecutionService(
            settings=settings,
            adapter=create_broker_adapter(settings),
        )
        result = service.submit_manual_order(self._request())
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, "broker_submit_unsupported")

    def test_idempotency_duplicate_rejection(self) -> None:
        settings = LiveExecutionSettings(
            enabled=True,
            allow_order_submission=True,
            submit_feature_enabled=True,
            status_feature_enabled=True,
            attempt_log_path=str(self.attempt_log_path),
        )
        service = LiveExecutionService(settings=settings, adapter=SubmitCapableFakeAdapter())
        first = service.submit_manual_order(self._request(idempotency_key="idem-dup"))
        second = service.submit_manual_order(self._request(idempotency_key="idem-dup"))
        self.assertEqual(first.rejection_code, "submit_rejected")
        self.assertFalse(second.accepted)
        self.assertEqual(second.rejection_code, "idempotency_key_duplicate")


if __name__ == "__main__":
    unittest.main()
