import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.config import APISettings


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class LiveExecutionEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=os.path.join(self.tempdir.name, "runs"),
            default_paper_trading_dir=os.path.join(self.tempdir.name, "paper"),
            enable_oanda_provider=False,
            feature_live_execution_submit_enabled=True,
        )
        self.client = TestClient(create_app(settings))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_status_and_validate_disabled_by_default(self) -> None:
        status = self.client.get("/api/v1/live-execution/status")
        self.assertEqual(status.status_code, 200)
        status_body = status.json()
        self.assertEqual(status_body["broker_name"], "null")
        self.assertEqual(status_body["state"], "disabled")
        self.assertFalse(status_body["enabled"])

        validation = self.client.post(
            "/api/v1/live-execution/intents/validate",
            json={
                "instrument": {"symbol": "EUR_USD", "asset_class": "forex"},
                "side": "buy",
                "order_type": "market",
                "quantity": 1000.0,
            },
        )
        self.assertEqual(validation.status_code, 200)
        body = validation.json()
        self.assertFalse(body["accepted"])
        self.assertIn("live_execution_disabled", body["reasons"])

    def test_submit_rejected_when_disabled(self) -> None:
        submit = self.client.post(
            "/api/v1/live-execution/intents/submit",
            json={
                "instrument": {"symbol": "EUR_USD", "asset_class": "forex"},
                "side": "buy",
                "order_type": "market",
                "quantity": 1000.0,
            },
        )
        self.assertEqual(submit.status_code, 409)
        body = submit.json()
        self.assertEqual(body["error"]["code"], "live_execution_manual_required")

    def test_submit_rejected_when_enabled_but_not_configured(self) -> None:
        self.tempdir.cleanup()
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=os.path.join(self.tempdir.name, "runs"),
            default_paper_trading_dir=os.path.join(self.tempdir.name, "paper"),
            enable_oanda_provider=False,
            live_execution_enabled=True,
            live_execution_allow_order_submission=True,
            live_execution_broker="oanda_stub",
            live_oanda_api_token=None,
            live_oanda_account_id=None,
            feature_live_execution_submit_enabled=True,
        )
        self.client = TestClient(create_app(settings))

        submit = self.client.post(
            "/api/v1/live-execution/intents/submit",
            json={
                "instrument": {"symbol": "EUR_USD", "asset_class": "forex"},
                "side": "buy",
                "order_type": "market",
                "quantity": 1000.0,
            },
        )
        self.assertEqual(submit.status_code, 409)
        body = submit.json()
        self.assertEqual(body["error"]["code"], "live_execution_manual_required")


if __name__ == "__main__":
    unittest.main()
