import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from config import AppSettings, build_safe_system_settings_snapshot  # noqa: E402


class SafetySnapshotTests(unittest.TestCase):
    def test_snapshot_redacts_secrets(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OANDA_API_TOKEN": "market-token",
                "LIVE_OANDA_API_TOKEN": "live-token",
                "LIVE_OANDA_ACCOUNT_ID": "acct-123",
                "LIVE_EXECUTION_ENABLED": "true",
                "LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION": "true",
                "FEATURE_LIVE_EXECUTION_SUBMIT_ENABLED": "true",
            },
            clear=True,
        ):
            app_settings = AppSettings.from_env()
        snapshot = build_safe_system_settings_snapshot(app_settings)
        payload = snapshot.to_dict()

        payload_text = str(payload)
        self.assertNotIn("market-token", payload_text)
        self.assertNotIn("live-token", payload_text)
        self.assertNotIn("acct-123", payload_text)
        self.assertTrue(payload["providers"]["oanda_market_data_configured"])
        self.assertTrue(payload["live_safety"]["credentials_configured"])
        self.assertTrue(payload["live_safety"]["effective_submission_enabled"])


if __name__ == "__main__":
    unittest.main()

