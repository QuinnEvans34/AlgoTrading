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

    def test_history_read_synthesizes_manifest_when_manifest_malformed(self) -> None:
        manifest_path = Path(self.tempdir.name) / self.run_id / "manifest.json"
        manifest_path.write_text("{bad-json", encoding="utf-8")

        read_resp = self.client.get(f"/api/v1/history/runs/{self.run_id}")
        self.assertEqual(read_resp.status_code, 200)
        read_body = read_resp.json()
        self.assertTrue(read_body["manifest"]["synthetic"])
        self.assertEqual(read_body["manifest"]["run_id"], self.run_id)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi is not installed")
class HistoryDbBackedEndpointsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "history.sqlite3"
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
        self.run_name = run_resp.json()["run_name"]
        self.run_id = run_resp.json()["run_id"]

    def tearDown(self) -> None:
        self.client.close()
        cached_manager = _database_manager_for_settings(self.settings.to_app_settings())
        if cached_manager is not None:
            cached_manager.engine.dispose()
        self.manager.engine.dispose()
        _database_manager_for_settings.cache_clear()
        self.tempdir.cleanup()

    def test_history_list_prefers_db_metadata_when_file_index_missing_entry(self) -> None:
        index_path = Path(self.tempdir.name) / "index.json"
        index_path.write_text(
            '{"schema_version": 1, "generated_at": "2026-03-26T12:00:00+00:00", "runs": [], "warnings": []}',
            encoding="utf-8",
        )

        response = self.client.get("/api/v1/history/runs?limit=20&offset=0&sort=started_desc")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(any(item["run_id"] == self.run_id for item in body["items"]))

    def test_history_read_uses_artifact_manifest_when_db_metadata_drifts(self) -> None:
        repository = SQLAlchemyResearchRunMetadataRepository(
            session_factory=self.manager.session_factory
        )
        record = repository.get_run_metadata(self.run_id)
        self.assertIsNotNone(record)
        assert record is not None
        repository.upsert_run_metadata(
            replace(
                record,
                run_name="db-drift-name",
                status="db-drift-status",
            )
        )

        response = self.client.get(f"/api/v1/history/runs/{self.run_id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["summary"]["run_name"], self.run_name)
        self.assertEqual(body["manifest"]["run_name"], self.run_name)
        self.assertNotEqual(body["manifest"]["run_name"], "db-drift-name")


if __name__ == "__main__":
    unittest.main()
