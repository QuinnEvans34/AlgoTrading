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
class LiveExecutionManualSubmitEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=os.path.join(self.tempdir.name, "runs"),
            default_paper_trading_dir=os.path.join(self.tempdir.name, "paper"),
            live_execution_enabled=False,
            live_execution_allow_order_submission=False,
            live_execution_broker="null",
            live_execution_confirmation_phrase="EXECUTE LIVE ORDER",
            live_execution_attempt_log_path=os.path.join(
                self.tempdir.name, "live", "attempts.jsonl"
            ),
            feature_live_execution_submit_enabled=True,
            feature_live_execution_status_enabled=True,
        )
        self.client = TestClient(create_app(settings))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _manual_payload(self) -> dict:
        return {
            "intent": {
                "instrument": {"symbol": "EUR_USD", "asset_class": "forex"},
                "side": "buy",
                "order_type": "market",
                "quantity": 1000.0,
            },
            "idempotency_key": "manual-1",
            "confirm_live_execution": True,
            "confirmation_text": "EXECUTE LIVE ORDER",
            "operator_id": "tester",
        }

    def test_readiness_endpoint_shape(self) -> None:
        response = self.client.get("/api/v1/live-execution/readiness")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("checks", body)
        self.assertIn("manual_submission_ready", body)
        self.assertIn("confirmation_phrase", body)
        self.assertEqual(body["confirmation_phrase"], "EXECUTE LIVE ORDER")
        self.assertFalse(body["manual_submission_ready"])

    def test_manual_submit_rejection_and_attempt_list(self) -> None:
        submit = self.client.post(
            "/api/v1/live-execution/manual-orders",
            json=self._manual_payload(),
        )
        self.assertEqual(submit.status_code, 200)
        body = submit.json()
        self.assertFalse(body["accepted"])
        self.assertEqual(body["rejection_code"], "live_execution_disabled")
        self.assertTrue(body["attempt_id"])

        attempts = self.client.get("/api/v1/live-execution/attempts?limit=10")
        self.assertEqual(attempts.status_code, 200)
        attempts_body = attempts.json()
        self.assertEqual(len(attempts_body["attempts"]), 1)
        self.assertEqual(
            attempts_body["attempts"][0]["rejection_code"],
            "live_execution_disabled",
        )


if __name__ == "__main__":
    unittest.main()
