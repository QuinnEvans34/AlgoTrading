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


def candle_payload(count: int = 160) -> list[dict]:
    out = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + 0.12 if i < 100 else price - 0.05
        out.append(
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
    return out


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class ResearchEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=self.tempdir.name,
            enable_oanda_provider=False,
        )
        self.client = TestClient(create_app(settings))
        self.base_payload = {
            "instrument": {"symbol": "AAPL", "asset_class": "stock"},
            "interval": "1d",
            "candle_source": {
                "source_type": "inline_candles",
                "candles": candle_payload(),
            },
        }

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_strategy_run_and_persisted_summary_lookup(self) -> None:
        payload = dict(self.base_payload)
        payload["run_config"] = {
            "persist_summary": True,
            "strict_failures": True,
        }
        response = self.client.post("/api/v1/research/strategy-runs", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["workflow_type"], "strategy_research")
        self.assertIn("step_results", body)
        run_id = body["run_id"]

        summary_response = self.client.get(f"/api/v1/research/runs/{run_id}/summary")
        self.assertEqual(summary_response.status_code, 200)
        persisted = summary_response.json()
        self.assertEqual(persisted["run_id"], run_id)

        list_response = self.client.get("/api/v1/research/runs")
        self.assertEqual(list_response.status_code, 200)
        runs = list_response.json()["runs"]
        self.assertTrue(any(item["run_id"] == run_id for item in runs))

    def test_ml_run(self) -> None:
        payload = dict(self.base_payload)
        payload["ml_spec"] = {
            "task_type": "classification",
            "label_specs": [
                {"label_type": "future_return", "horizon_bars": 5, "name": "ret_h5"},
                {"label_type": "direction", "horizon_bars": 5, "name": "dir_h5"},
            ],
            "target_label": "dir_h5",
            "model_specs": [
                {"model_id": "dummy_cls", "family": "dummy_classifier"},
            ],
        }
        response = self.client.post("/api/v1/research/ml-runs", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["workflow_type"], "ml_research")
        self.assertIn("ml", body)

    def test_hybrid_run(self) -> None:
        payload = dict(self.base_payload)
        payload["ml_spec"] = {
            "task_type": "classification",
            "label_specs": [
                {"label_type": "future_return", "horizon_bars": 3, "name": "ret_h3"},
                {"label_type": "direction", "horizon_bars": 3, "name": "dir_h3"},
            ],
            "target_label": "dir_h3",
            "model_specs": [
                {"model_id": "dummy_cls", "family": "dummy_classifier"},
            ],
        }
        response = self.client.post("/api/v1/research/hybrid-runs", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["workflow_type"], "hybrid_research")
        self.assertIn("strategy", body)
        self.assertIn("ml", body)


if __name__ == "__main__":
    unittest.main()

