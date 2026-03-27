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
class PaperTradingEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        paper_dir = os.path.join(self.tempdir.name, "paper")
        runs_dir = os.path.join(self.tempdir.name, "runs")
        settings = APISettings(
            default_run_output_dir=runs_dir,
            default_paper_trading_dir=paper_dir,
            enable_oanda_provider=False,
        )
        self.client = TestClient(create_app(settings))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_state_and_order_flow(self) -> None:
        state_resp = self.client.get("/api/v1/paper/state")
        self.assertEqual(state_resp.status_code, 200)
        body = state_resp.json()
        self.assertEqual(body["account"]["cash"], 100000.0)

        market_order = self.client.post(
            "/api/v1/paper/orders",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "side": "buy",
                "order_type": "market",
                "quantity": 10.0,
                "reference_price": 100.0,
            },
        )
        self.assertEqual(market_order.status_code, 200)
        order_body = market_order.json()
        self.assertEqual(order_body["order"]["status"], "filled")
        self.assertEqual(len(order_body["fills"]), 1)

        limit_order = self.client.post(
            "/api/v1/paper/orders",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "side": "sell",
                "order_type": "limit",
                "quantity": 10.0,
                "limit_price": 105.0,
            },
        )
        self.assertEqual(limit_order.status_code, 200)
        self.assertEqual(limit_order.json()["order"]["status"], "open")

        fill_limit = self.client.post(
            "/api/v1/paper/prices",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "price": 105.0,
            },
        )
        self.assertEqual(fill_limit.status_code, 200)
        self.assertGreaterEqual(len(fill_limit.json()["filled_order_ids"]), 1)

    def test_cancel_and_not_found(self) -> None:
        placed = self.client.post(
            "/api/v1/paper/orders",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "side": "buy",
                "order_type": "limit",
                "quantity": 1.0,
                "limit_price": 99.0,
                "reference_price": 101.0,
            },
        )
        self.assertEqual(placed.status_code, 200)
        order_id = placed.json()["order"]["order_id"]

        cancelled = self.client.post(f"/api/v1/paper/orders/{order_id}/cancel")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["order"]["status"], "cancelled")

        missing = self.client.post("/api/v1/paper/orders/does-not-exist/cancel")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "paper_order_not_found")

    def test_invalid_payload(self) -> None:
        bad = self.client.post(
            "/api/v1/paper/orders",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "side": "buy",
                "order_type": "market",
                "quantity": 0.0,
            },
        )
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["error"]["code"], "validation_error")


if __name__ == "__main__":
    unittest.main()

