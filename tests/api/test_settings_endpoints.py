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
class SettingsEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=os.path.join(self.tempdir.name, "runs"),
            default_paper_trading_dir=os.path.join(self.tempdir.name, "paper"),
            enable_oanda_provider=False,
            feature_live_execution_submit_enabled=False,
            live_execution_enabled=False,
        )
        self.client = TestClient(create_app(settings))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_system_settings_shape_and_redaction(self) -> None:
        response = self.client.get("/api/v1/settings/system")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("runtime", body)
        self.assertIn("feature_flags", body)
        self.assertIn("paper_defaults", body)
        self.assertIn("live_safety", body)
        self.assertIn("providers", body)
        self.assertFalse(body["live_safety"]["enabled"])
        self.assertFalse(body["live_safety"]["effective_submission_enabled"])
        payload_text = str(body)
        self.assertNotIn("token", payload_text.lower())

    def test_feature_flags_reflected_in_snapshot(self) -> None:
        response = self.client.get("/api/v1/settings/system")
        self.assertEqual(response.status_code, 200)
        flags = response.json()["feature_flags"]
        self.assertTrue(flags["research_api_enabled"])
        self.assertTrue(flags["paper_trading_enabled"])
        self.assertFalse(flags["live_execution_submit_enabled"])


if __name__ == "__main__":
    unittest.main()

