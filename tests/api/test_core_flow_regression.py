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


def candle_payload(count: int = 220) -> list[dict]:
    rows = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + (0.18 if i < 140 else -0.07)
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "open": price,
                "high": max(price, close) + 0.3,
                "low": min(price, close) - 0.3,
                "close": close,
                "volume": 2000.0 + i,
            }
        )
        ts += timedelta(days=1)
        price = close
    return rows


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class CoreFlowRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=os.path.join(self.tempdir.name, "runs"),
            default_paper_trading_dir=os.path.join(self.tempdir.name, "paper"),
            enable_oanda_provider=False,
            feature_history_api_enabled=True,
            feature_compare_api_enabled=True,
            feature_paper_trading_enabled=True,
        )
        self.client = TestClient(create_app(settings))
        self.base_run_payload = {
            "instrument": {"symbol": "AAPL", "asset_class": "stock"},
            "interval": "1d",
            "candle_source": {
                "source_type": "inline_candles",
                "candles": candle_payload(),
            },
            "run_config": {"persist_summary": True, "strict_failures": True},
        }

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _create_strategy_run(self, run_name: str) -> str:
        payload = dict(self.base_run_payload)
        payload["run_config"] = dict(payload["run_config"])
        payload["run_config"]["run_name"] = run_name
        response = self.client.post("/api/v1/research/strategy-runs", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["workflow_type"], "strategy_research")
        return body["run_id"]

    def _create_ml_run(self, run_name: str) -> str:
        payload = dict(self.base_run_payload)
        payload["run_config"] = dict(payload["run_config"])
        payload["run_config"]["run_name"] = run_name
        payload["ml_spec"] = {
            "task_type": "classification",
            "label_specs": [
                {"label_type": "future_return", "horizon_bars": 5, "name": "ret_h5"},
                {"label_type": "direction", "horizon_bars": 5, "name": "dir_h5"},
            ],
            "target_label": "dir_h5",
            "model_specs": [{"model_id": "dummy_cls", "family": "dummy_classifier"}],
        }
        response = self.client.post("/api/v1/research/ml-runs", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["workflow_type"], "ml_research")
        return body["run_id"]

    def test_strategy_ml_history_compare_and_paper_flow(self) -> None:
        strategy_a = self._create_strategy_run("strategy-A")
        strategy_b = self._create_strategy_run("strategy-B")
        ml_run = self._create_ml_run("ml-A")

        history_response = self.client.get("/api/v1/history/runs?limit=100&offset=0")
        self.assertEqual(history_response.status_code, 200)
        history = history_response.json()
        run_ids = {item["run_id"] for item in history["items"]}
        self.assertIn(strategy_a, run_ids)
        self.assertIn(strategy_b, run_ids)
        self.assertIn(ml_run, run_ids)

        strategy_detail = self.client.get(f"/api/v1/research/runs/{strategy_a}/detail")
        self.assertEqual(strategy_detail.status_code, 200)
        strategy_payload = strategy_detail.json()
        self.assertIsNotNone(strategy_payload["strategy_detail"])
        self.assertIsNone(strategy_payload["ml_detail"])

        history_read = self.client.get(f"/api/v1/history/runs/{strategy_a}")
        self.assertEqual(history_read.status_code, 200)
        history_payload = history_read.json()
        self.assertEqual(history_payload["manifest"]["run_id"], strategy_a)
        self.assertEqual(history_payload["summary"]["run_id"], strategy_a)

        ml_detail = self.client.get(f"/api/v1/research/runs/{ml_run}/detail")
        self.assertEqual(ml_detail.status_code, 200)
        ml_payload = ml_detail.json()
        self.assertIsNone(ml_payload["strategy_detail"])
        self.assertIsNotNone(ml_payload["ml_detail"])

        compare_response = self.client.post(
            "/api/v1/compare/runs",
            json={"run_ids": [strategy_a, strategy_b], "mode": "strategy"},
        )
        self.assertEqual(compare_response.status_code, 200)
        compare_payload = compare_response.json()
        self.assertEqual(compare_payload["mode"], "strategy")
        self.assertEqual(len(compare_payload["rows"]), 2)

        paper_state = self.client.get("/api/v1/paper/state")
        self.assertEqual(paper_state.status_code, 200)
        self.assertEqual(paper_state.json()["account"]["account_id"], "paper-main")

        paper_order = self.client.post(
            "/api/v1/paper/orders",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "side": "buy",
                "order_type": "market",
                "quantity": 5.0,
                "reference_price": 110.0,
            },
        )
        self.assertEqual(paper_order.status_code, 200)
        order_payload = paper_order.json()
        self.assertEqual(order_payload["order"]["status"], "filled")
        self.assertGreaterEqual(len(order_payload["fills"]), 1)


if __name__ == "__main__":
    unittest.main()
