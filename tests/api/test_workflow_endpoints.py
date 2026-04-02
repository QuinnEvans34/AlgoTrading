import importlib.util
import os
from pathlib import Path
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
    from api.dependencies import _database_manager_for_settings
    from persistence import Base, create_database_manager


def strategy_config_payload(symbol: str = "AAPL") -> dict:
    return {
        "config_type": "strategy",
        "name": "trend-template",
        "description": "saved from strategy lab",
        "config_schema_version": 1,
        "payload": {
            "instrument": {"symbol": symbol, "asset_class": "stock"},
            "interval": "1d",
            "candle_source": {"source_type": "inline_sample", "inline_bars": 220},
            "strategy_spec": {
                "strategy_id": "technical_rule_v1",
                "backtest_config": {
                    "warmup_bars": 80,
                    "min_signal_confidence": 0.1,
                },
            },
            "run_config": {
                "run_name": "trend-run-default",
                "persist_summary": True,
                "strict_failures": True,
            },
        },
    }


def ml_config_payload(symbol: str = "MSFT") -> dict:
    return {
        "config_type": "ml",
        "name": "ml-template",
        "description": None,
        "config_schema_version": 1,
        "payload": {
            "instrument": {"symbol": symbol, "asset_class": "stock"},
            "interval": "1d",
            "candle_source": {
                "source_type": "market_data_fetch",
                "provider_name": "oanda",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-03-01T00:00:00Z",
            },
            "ml_spec": {
                "task_type": "classification",
                "label_specs": [
                    {"label_type": "future_return", "horizon_bars": 3, "name": "ret_h3"},
                    {"label_type": "direction", "horizon_bars": 3, "name": "dir_h3"},
                ],
                "target_label": "dir_h3",
                "model_specs": [{"model_id": "dummy_cls", "family": "dummy_classifier"}],
            },
            "run_config": {
                "run_name": "ml-run-default",
                "persist_summary": False,
                "strict_failures": True,
            },
        },
    }


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class WorkflowEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "workflow.sqlite3"
        self.settings = APISettings(
            default_run_output_dir=self.tempdir.name,
            enable_oanda_provider=False,
            database_enabled=True,
            database_url=f"sqlite+pysqlite:///{self.db_path.as_posix()}",
        )
        manager = create_database_manager(self.settings.to_app_settings().database)
        assert manager is not None
        self.manager = manager
        Base.metadata.create_all(manager.engine)
        self.client = TestClient(create_app(self.settings))

    def tearDown(self) -> None:
        self.client.close()
        cached_manager = _database_manager_for_settings(self.settings.to_app_settings())
        if cached_manager is not None:
            cached_manager.engine.dispose()
        self.manager.engine.dispose()
        _database_manager_for_settings.cache_clear()
        self.tempdir.cleanup()

    def test_saved_config_crud_and_version_validation(self) -> None:
        created = self.client.post(
            "/api/v1/workflow/saved-configs",
            json=strategy_config_payload(),
        )
        self.assertEqual(created.status_code, 200)
        created_body = created.json()
        config_id = created_body["id"]
        self.assertEqual(created_body["config_type"], "strategy")
        self.assertEqual(created_body["payload"]["instrument"]["symbol"], "AAPL")

        listed = self.client.get("/api/v1/workflow/saved-configs?config_type=strategy")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()["items"]), 1)

        loaded = self.client.get(f"/api/v1/workflow/saved-configs/{config_id}")
        self.assertEqual(loaded.status_code, 200)
        self.assertEqual(loaded.json()["name"], "trend-template")
        self.assertIsNotNone(loaded.json()["last_used_at"])

        update_payload = strategy_config_payload("NVDA")
        update_payload["name"] = "trend-template-v2"
        updated = self.client.put(
            f"/api/v1/workflow/saved-configs/{config_id}",
            json=update_payload,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["instrument_symbol"], "NVDA")
        self.assertEqual(updated.json()["payload"]["instrument"]["symbol"], "NVDA")

        invalid_version_payload = strategy_config_payload()
        invalid_version_payload["config_schema_version"] = 99
        invalid = self.client.post(
            "/api/v1/workflow/saved-configs",
            json=invalid_version_payload,
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["error"]["code"], "saved_config_invalid")

        deleted = self.client.delete(f"/api/v1/workflow/saved-configs/{config_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["deleted"])

    def test_ml_config_and_watchlist_recent_endpoints(self) -> None:
        created = self.client.post(
            "/api/v1/workflow/saved-configs",
            json=ml_config_payload(),
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["config_type"], "ml")

        watchlisted = self.client.post(
            "/api/v1/workflow/watchlist/items",
            json={"symbol": "MSFT", "asset_class": "stock", "source_context": "ml_page"},
        )
        self.assertEqual(watchlisted.status_code, 200)
        self.assertEqual(watchlisted.json()["symbol"], "MSFT")

        watchlist = self.client.get("/api/v1/workflow/watchlist")
        self.assertEqual(watchlist.status_code, 200)
        self.assertEqual(len(watchlist.json()["items"]), 1)

        recent_asset = self.client.post(
            "/api/v1/workflow/recent-assets/touch",
            json={"symbol": "MSFT", "asset_class": "stock", "source_context": "ml_submit"},
        )
        self.assertEqual(recent_asset.status_code, 200)

        recent_assets = self.client.get("/api/v1/workflow/recent-assets")
        self.assertEqual(recent_assets.status_code, 200)
        self.assertEqual(len(recent_assets.json()["items"]), 1)

        recent_compare = self.client.post(
            "/api/v1/workflow/recent-compares/touch",
            json={"compare_mode": "strategy", "run_ids": ["run-001", "run-002"]},
        )
        self.assertEqual(recent_compare.status_code, 200)

        recent_compares = self.client.get("/api/v1/workflow/recent-compares")
        self.assertEqual(recent_compares.status_code, 200)
        self.assertEqual(len(recent_compares.json()["items"]), 1)

        deleted = self.client.delete("/api/v1/workflow/watchlist/items/stock/MSFT")
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["deleted"])


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class WorkflowEndpointsUnavailableTests(unittest.TestCase):
    def test_workflow_endpoints_report_unavailable_without_database(self) -> None:
        client = TestClient(create_app(APISettings(enable_oanda_provider=False)))
        try:
            response = client.get("/api/v1/workflow/saved-configs")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(
                response.json()["error"]["code"],
                "workflow_persistence_unavailable",
            )
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
