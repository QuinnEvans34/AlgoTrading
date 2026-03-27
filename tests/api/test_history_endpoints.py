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


def candle_payload(count: int = 180) -> list[dict]:
    rows = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + (0.15 if i < 120 else -0.03)
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "open": price,
                "high": max(price, close) + 0.2,
                "low": min(price, close) - 0.2,
                "close": close,
                "volume": 1000.0 + i,
            }
        )
        ts += timedelta(days=1)
        price = close
    return rows


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class HistoryEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=self.tempdir.name,
            enable_oanda_provider=False,
        )
        self.client = TestClient(create_app(settings))
        run_resp = self.client.post(
            "/api/v1/research/strategy-runs",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "interval": "1d",
                "candle_source": {"source_type": "inline_candles", "candles": candle_payload()},
                "run_config": {"persist_summary": True, "strict_failures": True},
            },
        )
        self.assertEqual(run_resp.status_code, 200)
        self.run_id = run_resp.json()["run_id"]

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_history_list_and_read(self) -> None:
        list_resp = self.client.get("/api/v1/history/runs?limit=20&offset=0&sort=started_desc")
        self.assertEqual(list_resp.status_code, 200)
        body = list_resp.json()
        self.assertIn("items", body)
        self.assertGreaterEqual(body["total"], 1)
        self.assertTrue(any(item["run_id"] == self.run_id for item in body["items"]))

        read_resp = self.client.get(f"/api/v1/history/runs/{self.run_id}")
        self.assertEqual(read_resp.status_code, 200)
        read_body = read_resp.json()
        self.assertEqual(read_body["manifest"]["run_id"], self.run_id)
        self.assertEqual(read_body["summary"]["run_id"], self.run_id)
        self.assertIn("detail", read_body)

    def test_history_missing_and_invalid(self) -> None:
        missing = self.client.get("/api/v1/history/runs/does-not-exist")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "run_not_found")

        invalid = self.client.get("/api/v1/history/runs/..%5Cbad")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["error"]["code"], "invalid_run_id")


if __name__ == "__main__":
    unittest.main()
