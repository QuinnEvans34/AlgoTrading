import os
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import BacktestConfig  # noqa: E402
from config import DatabaseSettings  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from persistence import (  # noqa: E402
    Base,
    PersistenceUnavailableError,
    SQLAlchemyResearchRunMetadataRepository,
    create_database_manager,
)
from research import (  # noqa: E402
    InlineCandleSource,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    RunStatus,
    StrategyWorkflowSpec,
    get_run_detail,
    get_run_manifest,
    list_run_history,
    load_saved_run_bundle,
)
from persistence.research_runs import ResearchRunMetadataRepository  # noqa: E402


class FailingMetadataRepository(ResearchRunMetadataRepository):
    def upsert_run_metadata(self, record):  # noqa: ANN001, D401
        raise PersistenceUnavailableError("db unavailable")

    def get_run_metadata(self, run_id: str):  # noqa: ANN001, D401
        raise PersistenceUnavailableError("db unavailable")

    def list_run_metadata(self, query):  # noqa: ANN001, D401
        raise PersistenceUnavailableError("db unavailable")

    def list_known_run_ids(self) -> set[str]:
        raise PersistenceUnavailableError("db unavailable")


def make_candles(count: int = 220) -> tuple[Candle, ...]:
    rows: list[Candle] = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + (0.2 if i < 150 else -0.05)
        rows.append(
            Candle(
                timestamp=ts,
                open=price,
                high=max(price, close) + 0.2,
                low=min(price, close) - 0.2,
                close=close,
                volume=1000.0 + i,
            )
        )
        ts += timedelta(days=1)
        price = close
    return tuple(rows)


class HistoryStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.output_dir = self.tempdir.name
        self.runner = ResearchRunner()
        db_path = Path(self.tempdir.name) / "metadata.sqlite3"
        manager = create_database_manager(
            DatabaseSettings(
                enabled=True,
                url=f"sqlite+pysqlite:///{db_path.as_posix()}",
                echo=False,
            )
        )
        assert manager is not None
        self.manager = manager
        Base.metadata.create_all(manager.engine)
        self.metadata_repository = SQLAlchemyResearchRunMetadataRepository(
            session_factory=manager.session_factory
        )
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        self.request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
            instrument=self.instrument,
            interval=BarInterval.D1,
            candle_source=InlineCandleSource(candles=make_candles()),
            strategy_spec=StrategyWorkflowSpec(
                backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
            ),
            run_config=ResearchRunConfig(
                persist_summary=True,
                output_dir=self.output_dir,
                strict_failures=True,
            ),
        )

    def tearDown(self) -> None:
        self.manager.engine.dispose()
        self.tempdir.cleanup()

    def test_runner_persists_manifest_and_index(self) -> None:
        artifact = self.runner.run(self.request)
        self.assertEqual(artifact.status, RunStatus.SUCCESS)
        run_root = Path(self.output_dir) / artifact.run_id
        self.assertTrue((run_root / "summary.json").exists())
        self.assertTrue((run_root / "detail.json").exists())
        self.assertTrue((run_root / "manifest.json").exists())
        self.assertTrue((Path(self.output_dir) / "index.json").exists())

        history = list_run_history(Path(self.output_dir), query=self._query())
        self.assertGreaterEqual(history.total, 1)
        self.assertTrue(any(item.run_id == artifact.run_id for item in history.items))

    def test_corrupt_index_triggers_rebuild(self) -> None:
        artifact = self.runner.run(self.request)
        index_path = Path(self.output_dir) / "index.json"
        index_path.write_text("{bad-json", encoding="utf-8")
        history = list_run_history(Path(self.output_dir), query=self._query())
        self.assertGreaterEqual(history.total, 1)
        self.assertTrue(any(item.run_id == artifact.run_id for item in history.items))
        self.assertTrue(any("index_corrupt_rebuilt" in warning for warning in history.warnings))

    def test_missing_or_malformed_manifest_is_synthesized(self) -> None:
        artifact = self.runner.run(self.request)
        manifest_path = Path(self.output_dir) / artifact.run_id / "manifest.json"

        manifest_path.unlink()
        synthetic_missing = get_run_manifest(Path(self.output_dir), artifact.run_id)
        self.assertTrue(synthetic_missing["synthetic"])
        self.assertEqual(synthetic_missing["run_id"], artifact.run_id)

        manifest_path.write_text("{bad-json", encoding="utf-8")
        synthetic_bad = get_run_manifest(Path(self.output_dir), artifact.run_id)
        self.assertTrue(synthetic_bad["synthetic"])
        self.assertEqual(synthetic_bad["run_name"], artifact.run_name)

    def test_malformed_detail_falls_back_to_summary_only(self) -> None:
        artifact = self.runner.run(self.request)
        detail_path = Path(self.output_dir) / artifact.run_id / "detail.json"
        detail_path.write_text("{bad-json", encoding="utf-8")

        detail = get_run_detail(Path(self.output_dir), artifact.run_id)
        self.assertEqual(detail["summary"]["run_id"], artifact.run_id)
        self.assertIsNone(detail["strategy_detail"])
        self.assertIsNone(detail["ml_detail"])

    def test_runner_dual_writes_db_metadata_when_repository_configured(self) -> None:
        runner = ResearchRunner(metadata_repository=self.metadata_repository)
        artifact = runner.run(self.request)

        loaded = self.metadata_repository.get_run_metadata(artifact.run_id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.run_id, artifact.run_id)
        self.assertEqual(loaded.summary_path, f"{artifact.run_id}/summary.json")

    def test_runner_keeps_artifacts_when_db_write_fails(self) -> None:
        runner = ResearchRunner(metadata_repository=FailingMetadataRepository())
        artifact = runner.run(self.request)

        self.assertEqual(artifact.status, RunStatus.SUCCESS)
        self.assertTrue((Path(self.output_dir) / artifact.run_id / "summary.json").exists())
        self.assertTrue((Path(self.output_dir) / artifact.run_id / "detail.json").exists())

    def test_history_listing_falls_back_when_db_unavailable(self) -> None:
        artifact = self.runner.run(self.request)
        history = list_run_history(
            Path(self.output_dir),
            query=self._query(),
            metadata_repository=FailingMetadataRepository(),
        )
        self.assertTrue(any(item.run_id == artifact.run_id for item in history.items))
        self.assertIn("db_metadata_unavailable_fallback", history.warnings)

    def test_db_primary_history_includes_legacy_only_runs_without_duplicates(self) -> None:
        db_runner = ResearchRunner(metadata_repository=self.metadata_repository)
        db_artifact = db_runner.run(self.request)
        legacy_artifact = self.runner.run(self.request)
        index_path = Path(self.output_dir) / "index.json"
        index_path.write_text(
            '{"schema_version": 1, "generated_at": "2026-03-27T12:00:00+00:00", "runs": [], "warnings": []}',
            encoding="utf-8",
        )

        history = list_run_history(
            Path(self.output_dir),
            query=self._query(),
            metadata_repository=self.metadata_repository,
        )

        run_ids = [item.run_id for item in history.items]
        self.assertEqual(history.total, 2)
        self.assertCountEqual(run_ids, [db_artifact.run_id, legacy_artifact.run_id])
        self.assertEqual(len(run_ids), len(set(run_ids)))

    def test_db_primary_history_uses_run_id_tiebreak_for_mixed_sources(self) -> None:
        db_runner = ResearchRunner(metadata_repository=self.metadata_repository)
        db_artifact = db_runner.run(self.request)
        legacy_artifact = self.runner.run(self.request)
        legacy_bundle = load_saved_run_bundle(Path(self.output_dir), legacy_artifact.run_id)
        db_record = self.metadata_repository.get_run_metadata(db_artifact.run_id)
        self.assertIsNotNone(db_record)
        assert db_record is not None
        self.metadata_repository.upsert_run_metadata(
            replace(
                db_record,
                started_at=legacy_bundle.summary.started_at,
                updated_at=legacy_bundle.summary.started_at,
            )
        )

        history = list_run_history(
            Path(self.output_dir),
            query=self._query(),
            metadata_repository=self.metadata_repository,
        )

        expected = sorted([db_artifact.run_id, legacy_artifact.run_id], reverse=True)
        self.assertEqual([item.run_id for item in history.items], expected)

    def test_history_read_uses_artifact_manifest_when_db_metadata_drifts(self) -> None:
        db_runner = ResearchRunner(metadata_repository=self.metadata_repository)
        artifact = db_runner.run(self.request)
        record = self.metadata_repository.get_run_metadata(artifact.run_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.metadata_repository.upsert_run_metadata(
            replace(
                record,
                run_name="db-drift-name",
                status="db-drift-status",
                manifest_synthetic=False,
            )
        )

        bundle = load_saved_run_bundle(
            Path(self.output_dir),
            artifact.run_id,
            metadata=self.metadata_repository.get_run_metadata(artifact.run_id),
        )

        self.assertEqual(bundle.summary.run_name, artifact.run_name)
        self.assertEqual(bundle.manifest.run_name, artifact.run_name)
        self.assertEqual(bundle.manifest.status, artifact.status.value)

    @staticmethod
    def _query():
        from research import RunHistoryQuery

        return RunHistoryQuery(limit=100, offset=0)


if __name__ == "__main__":
    unittest.main()
