import importlib.util
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.config import APISettings


def tiny_candles(count: int = 5) -> list[dict]:
    rows = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for _ in range(count):
        close = price + 0.1
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "open": price,
                "high": close + 0.1,
                "low": price - 0.1,
                "close": close,
                "volume": 1000.0,
            }
        )
        ts += timedelta(days=1)
        price = close
    return rows


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class APIErrorHandlingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=self.tempdir.name,
            enable_oanda_provider=False,
        )
        self.client = TestClient(create_app(settings))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_validation_error_shape(self) -> None:
        response = self.client.post(
            "/api/v1/research/strategy-runs",
            json={"interval": "1d"},
        )
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "validation_error")

    def test_provider_not_found_error(self) -> None:
        response = self.client.post(
            "/api/v1/market-data/historical-preview",
            json={
                "provider_name": "unknown_provider",
                "instrument": {"symbol": "EUR_USD", "asset_class": "forex"},
                "interval": "1h",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-02T00:00:00Z",
            },
        )
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["error"]["code"], "provider_not_found")

    def test_missing_run_summary_error(self) -> None:
        response = self.client.get("/api/v1/research/runs/does-not-exist/summary")
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["error"]["code"], "run_summary_not_found")


if __name__ == "__main__":
    unittest.main()

