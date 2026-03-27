import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from config import AppSettings  # noqa: E402


class AppSettingsTests(unittest.TestCase):
    def test_defaults_with_missing_optional_values(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = AppSettings.from_env()
        self.assertEqual(settings.api.app_name, "capstone-research-api")
        self.assertEqual(settings.storage.run_output_dir, "artifacts/research_runs")
        self.assertFalse(settings.live_safety.enabled)
        self.assertIsNone(settings.live_safety.oanda_api_token)
        self.assertTrue(settings.feature_flags.research_api_enabled)
        self.assertFalse(settings.feature_flags.live_execution_submit_enabled)

    def test_typed_env_parsing(self) -> None:
        with patch.dict(
            os.environ,
            {
                "API_PORT": "9001",
                "API_CORS_ALLOWED_ORIGINS": "http://localhost:5173, http://127.0.0.1:3000",
                "API_PAPER_DEFAULT_INITIAL_CASH": "250000.5",
                "API_PAPER_DEFAULT_ALLOW_SHORT": "true",
                "LIVE_EXECUTION_ENABLED": "1",
                "LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION": "yes",
                "FEATURE_LIVE_EXECUTION_SUBMIT_ENABLED": "true",
            },
            clear=True,
        ):
            settings = AppSettings.from_env()
        self.assertEqual(settings.api.port, 9001)
        self.assertEqual(len(settings.api.cors_allowed_origins), 2)
        self.assertAlmostEqual(settings.paper_defaults.initial_cash, 250000.5)
        self.assertTrue(settings.paper_defaults.allow_short)
        self.assertTrue(settings.live_safety.enabled)
        self.assertTrue(settings.live_safety.allow_order_submission)
        self.assertTrue(settings.feature_flags.live_execution_submit_enabled)


if __name__ == "__main__":
    unittest.main()

