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
class SafetyDefaultsRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=os.path.join(self.tempdir.name, "runs"),
            default_paper_trading_dir=os.path.join(self.tempdir.name, "paper"),
            live_execution_attempt_log_path=os.path.join(
                self.tempdir.name, "live", "attempts.jsonl"
            ),
            enable_oanda_provider=False,
        )
        self.client = TestClient(create_app(settings))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_live_and_settings_defaults_are_fail_closed(self) -> None:
        settings_response = self.client.get("/api/v1/settings/system")
        self.assertEqual(settings_response.status_code, 200)
        settings_payload = settings_response.json()
        self.assertFalse(settings_payload["live_safety"]["enabled"])
        self.assertFalse(settings_payload["live_safety"]["allow_order_submission"])
        self.assertFalse(settings_payload["live_safety"]["effective_submission_enabled"])
        self.assertFalse(settings_payload["live_safety"]["submit_feature_enabled"])
        self.assertIn("confirmation_phrase", settings_payload["live_safety"])
        self.assertIn("attempt_log_path", settings_payload["live_safety"])

        status_response = self.client.get("/api/v1/live-execution/status")
        self.assertEqual(status_response.status_code, 200)
        status_payload = status_response.json()
        self.assertFalse(status_payload["enabled"])
        self.assertEqual(status_payload["state"], "disabled")

        readiness_response = self.client.get("/api/v1/live-execution/readiness")
        self.assertEqual(readiness_response.status_code, 200)
        readiness_payload = readiness_response.json()
        self.assertFalse(readiness_payload["manual_submission_ready"])
        self.assertTrue(any(not check["passed"] for check in readiness_payload["checks"]))

    def test_live_submit_endpoints_reject_by_default(self) -> None:
        legacy_submit = self.client.post(
            "/api/v1/live-execution/intents/submit",
            json={
                "instrument": {"symbol": "EUR_USD", "asset_class": "forex"},
                "side": "buy",
                "order_type": "market",
                "quantity": 1000.0,
            },
        )
        self.assertEqual(legacy_submit.status_code, 403)
        self.assertEqual(
            legacy_submit.json()["error"]["code"], "live_execution_submit_disabled"
        )

        manual_submit = self.client.post(
            "/api/v1/live-execution/manual-orders",
            json={
                "intent": {
                    "instrument": {"symbol": "EUR_USD", "asset_class": "forex"},
                    "side": "buy",
                    "order_type": "market",
                    "quantity": 1000.0,
                },
                "idempotency_key": "default-safe-check",
                "confirm_live_execution": True,
                "confirmation_text": "EXECUTE LIVE ORDER",
            },
        )
        self.assertEqual(manual_submit.status_code, 403)
        self.assertEqual(
            manual_submit.json()["error"]["code"], "live_execution_submit_disabled"
        )


if __name__ == "__main__":
    unittest.main()
