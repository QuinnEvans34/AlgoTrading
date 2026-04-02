import importlib.util
import os
from pathlib import Path
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
    from api.dependencies import _database_manager_for_settings
    from persistence import Base, create_database_manager


def candle_payload(count: int = 200) -> list[dict]:
    rows = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + (0.12 if i < 130 else -0.06)
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
class CompareEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        settings = APISettings(
            default_run_output_dir=self.tempdir.name,
            enable_oanda_provider=False,
        )
        self.client = TestClient(create_app(settings))
        self.strategy_run_ids = [self._create_strategy_run(), self._create_strategy_run()]

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _create_strategy_run(self) -> str:
        response = self.client.post(
            "/api/v1/research/strategy-runs",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "interval": "1d",
                "candle_source": {"source_type": "inline_candles", "candles": candle_payload()},
                "run_config": {"persist_summary": True, "strict_failures": True},
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["run_id"]

    def _create_ml_run(self) -> str:
        response = self.client.post(
            "/api/v1/research/ml-runs",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "interval": "1d",
                "candle_source": {"source_type": "inline_candles", "candles": candle_payload()},
                "ml_spec": {
                    "task_type": "classification",
                    "label_specs": [
                        {"label_type": "future_return", "horizon_bars": 3, "name": "ret_h3"},
                        {"label_type": "direction", "horizon_bars": 3, "name": "dir_h3"},
                    ],
                    "target_label": "dir_h3",
                    "model_specs": [{"model_id": "dummy_cls", "family": "dummy_classifier"}],
                },
                "run_config": {"persist_summary": True, "strict_failures": True},
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["run_id"]

    def test_compare_strategy_runs(self) -> None:
        response = self.client.post(
            "/api/v1/compare/runs",
            json={"run_ids": self.strategy_run_ids, "mode": "strategy"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "strategy")
        self.assertEqual(len(body["rows"]), 2)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class CompareDbBackedEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "compare.sqlite3"
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
        self.strategy_run_ids = [self._create_strategy_run(), self._create_strategy_run()]

    def tearDown(self) -> None:
        self.client.close()
        cached_manager = _database_manager_for_settings(self.settings.to_app_settings())
        if cached_manager is not None:
            cached_manager.engine.dispose()
        self.manager.engine.dispose()
        _database_manager_for_settings.cache_clear()
        self.tempdir.cleanup()

    def _create_strategy_run(self) -> str:
        response = self.client.post(
            "/api/v1/research/strategy-runs",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "interval": "1d",
                "candle_source": {"source_type": "inline_candles", "candles": candle_payload()},
                "run_config": {"persist_summary": True, "strict_failures": True},
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["run_id"]

    def _create_ml_run(self) -> str:
        response = self.client.post(
            "/api/v1/research/ml-runs",
            json={
                "instrument": {"symbol": "AAPL", "asset_class": "stock"},
                "interval": "1d",
                "candle_source": {"source_type": "inline_candles", "candles": candle_payload()},
                "ml_spec": {
                    "task_type": "classification",
                    "label_specs": [
                        {"label_type": "future_return", "horizon_bars": 3, "name": "ret_h3"},
                        {"label_type": "direction", "horizon_bars": 3, "name": "dir_h3"},
                    ],
                    "target_label": "dir_h3",
                    "model_specs": [{"model_id": "dummy_cls", "family": "dummy_classifier"}],
                },
                "run_config": {"persist_summary": True, "strict_failures": True},
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["run_id"]

    def test_compare_with_db_metadata_and_missing_detail_still_succeeds(self) -> None:
        detail_path = Path(self.tempdir.name) / self.strategy_run_ids[0] / "detail.json"
        detail_path.unlink()

        response = self.client.post(
            "/api/v1/compare/runs",
            json={"run_ids": self.strategy_run_ids, "mode": "strategy"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "strategy")
        self.assertEqual(len(body["rows"]), 2)

    def test_compare_mixed_runs_rejected(self) -> None:
        ml_run = self._create_ml_run()
        response = self.client.post(
            "/api/v1/compare/runs",
            json={"run_ids": [self.strategy_run_ids[0], ml_run], "mode": "auto"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "compare_invalid")

    def test_compare_missing_run(self) -> None:
        response = self.client.post(
            "/api/v1/compare/runs",
            json={"run_ids": [self.strategy_run_ids[0], "does-not-exist"], "mode": "strategy"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "run_not_found")

    def test_compare_strategy_runs_with_malformed_detail_still_succeeds(self) -> None:
        detail_path = Path(self.tempdir.name) / self.strategy_run_ids[0] / "detail.json"
        detail_path.write_text("{bad-json", encoding="utf-8")

        response = self.client.post(
            "/api/v1/compare/runs",
            json={"run_ids": self.strategy_run_ids, "mode": "strategy"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "strategy")
        self.assertEqual(len(body["rows"]), 2)


if __name__ == "__main__":
    unittest.main()
