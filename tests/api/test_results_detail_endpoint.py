import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import replace
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
    from persistence import (
        Base,
        SQLAlchemyResearchRunMetadataRepository,
        create_database_manager,
    )


def candle_payload(count: int = 180) -> list[dict]:
    out = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + 0.15 if i < 120 else price - 0.04
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
class ResultsDetailEndpointTests(unittest.TestCase):
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
            "run_config": {"persist_summary": True, "strict_failures": True},
        }

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_detail_endpoint_returns_strategy_detail(self) -> None:
        run_response = self.client.post("/api/v1/research/strategy-runs", json=self.base_payload)
        self.assertEqual(run_response.status_code, 200)
        run_id = run_response.json()["run_id"]

        detail_response = self.client.get(f"/api/v1/research/runs/{run_id}/detail")
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.json()
        self.assertEqual(body["summary"]["run_id"], run_id)
        self.assertIsNotNone(body["strategy_detail"])
        self.assertIsNone(body["ml_detail"])
        self.assertGreater(len(body["strategy_detail"]["equity_curve"]), 0)
        self.assertIn("trade_analysis", body["strategy_detail"])

    def test_detail_endpoint_falls_back_to_summary_only_when_detail_missing(self) -> None:
        run_response = self.client.post("/api/v1/research/strategy-runs", json=self.base_payload)
        self.assertEqual(run_response.status_code, 200)
        run_id = run_response.json()["run_id"]
        detail_path = Path(self.tempdir.name) / run_id / "detail.json"
        detail_path.unlink()

        detail_response = self.client.get(f"/api/v1/research/runs/{run_id}/detail")
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.json()
        self.assertEqual(body["summary"]["run_id"], run_id)
        self.assertIsNone(body["strategy_detail"])
        self.assertIsNone(body["ml_detail"])

    def test_detail_endpoint_falls_back_to_summary_only_when_detail_malformed(self) -> None:
        run_response = self.client.post("/api/v1/research/strategy-runs", json=self.base_payload)
        self.assertEqual(run_response.status_code, 200)
        run_id = run_response.json()["run_id"]
        detail_path = Path(self.tempdir.name) / run_id / "detail.json"
        detail_path.write_text("{bad-json", encoding="utf-8")

        detail_response = self.client.get(f"/api/v1/research/runs/{run_id}/detail")
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.json()
        self.assertEqual(body["summary"]["run_id"], run_id)
        self.assertIsNone(body["strategy_detail"])
        self.assertIsNone(body["ml_detail"])

    def test_detail_endpoint_not_found_and_invalid_id(self) -> None:
        missing = self.client.get("/api/v1/research/runs/does-not-exist/detail")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "run_detail_not_found")

        invalid = self.client.get("/api/v1/research/runs/..%5Cbad/detail")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["error"]["code"], "invalid_run_id")


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class ResultsDetailDbBackedEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "detail.sqlite3"
        self.settings = APISettings(
            default_run_output_dir=self.tempdir.name,
            enable_oanda_provider=False,
            database_enabled=True,
            database_url=f"sqlite+pysqlite:///{db_path.as_posix()}",
        )
        manager = create_database_manager(self.settings.to_app_settings().database)
        assert manager is not None
        self.manager = manager
        Base.metadata.create_all(manager.engine)
        self.client = TestClient(create_app(self.settings))
        self.base_payload = {
            "instrument": {"symbol": "AAPL", "asset_class": "stock"},
            "interval": "1d",
            "candle_source": {
                "source_type": "inline_candles",
                "candles": candle_payload(),
            },
            "run_config": {"persist_summary": True, "strict_failures": True},
        }

    def tearDown(self) -> None:
        self.client.close()
        cached_manager = _database_manager_for_settings(self.settings.to_app_settings())
        if cached_manager is not None:
            cached_manager.engine.dispose()
        self.manager.engine.dispose()
        _database_manager_for_settings.cache_clear()
        self.tempdir.cleanup()

    def test_detail_endpoint_still_reads_file_backed_detail_when_metadata_is_db_backed(self) -> None:
        run_response = self.client.post("/api/v1/research/strategy-runs", json=self.base_payload)
        self.assertEqual(run_response.status_code, 200)
        run_id = run_response.json()["run_id"]

        detail_response = self.client.get(f"/api/v1/research/runs/{run_id}/detail")
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.json()
        self.assertEqual(body["summary"]["run_id"], run_id)
        self.assertIsNotNone(body["strategy_detail"])

    def test_detail_endpoint_uses_artifact_paths_when_db_metadata_drifts(self) -> None:
        run_response = self.client.post("/api/v1/research/strategy-runs", json=self.base_payload)
        self.assertEqual(run_response.status_code, 200)
        run_id = run_response.json()["run_id"]
        repository = SQLAlchemyResearchRunMetadataRepository(
            session_factory=self.manager.session_factory
        )
        record = repository.get_run_metadata(run_id)
        self.assertIsNotNone(record)
        assert record is not None
        repository.upsert_run_metadata(
            replace(
                record,
                detail_path="missing/detail.json",
                manifest_path="missing/manifest.json",
            )
        )

        detail_response = self.client.get(f"/api/v1/research/runs/{run_id}/detail")
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.json()
        self.assertEqual(body["summary"]["run_id"], run_id)
        self.assertIsNotNone(body["strategy_detail"])


if __name__ == "__main__":
    unittest.main()
