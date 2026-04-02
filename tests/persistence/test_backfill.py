import os
import sys
import tempfile
import unittest
from dataclasses import replace
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
    SQLAlchemyResearchRunMetadataRepository,
    backfill_research_run_metadata,
    build_run_metadata_record,
    create_database_manager,
    report_research_run_metadata_transition,
)
from research import (  # noqa: E402
    InlineCandleSource,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    StrategyWorkflowSpec,
    load_saved_run_bundle,
)


def make_candles() -> tuple[Candle, ...]:
    from datetime import datetime, timedelta, timezone

    rows: list[Candle] = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(180):
        close = price + (0.1 if i < 120 else -0.03)
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


class BackfillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.tempdir.name) / "runs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.runner = ResearchRunner()
        self.instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        self.run_id = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=InlineCandleSource(candles=make_candles()),
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
                ),
                run_config=ResearchRunConfig(
                    persist_summary=True,
                    output_dir=str(self.output_dir),
                    strict_failures=True,
                ),
            )
        ).run_id

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
        self.repository = SQLAlchemyResearchRunMetadataRepository(
            session_factory=manager.session_factory
        )

    def tearDown(self) -> None:
        self.manager.engine.dispose()
        self.tempdir.cleanup()

    def test_backfill_imports_existing_artifacts_idempotently(self) -> None:
        first = backfill_research_run_metadata(
            root_dir=self.output_dir,
            repository=self.repository,
        )
        second = backfill_research_run_metadata(
            root_dir=self.output_dir,
            repository=self.repository,
        )

        self.assertEqual(first.inserted_count, 1)
        self.assertEqual(first.updated_count, 0)
        self.assertEqual(first.unchanged_count, 0)
        self.assertEqual(first.skipped_count, 0)
        self.assertEqual(second.inserted_count, 0)
        self.assertEqual(second.updated_count, 0)
        self.assertEqual(second.unchanged_count, 1)
        self.assertEqual(second.skipped_count, 0)
        self.assertEqual(len(self.repository.list_known_run_ids()), 1)

    def test_backfill_updates_drifted_db_rows_from_artifacts(self) -> None:
        bundle = load_saved_run_bundle(self.output_dir, self.run_id)
        original = build_run_metadata_record(
            root_dir=self.output_dir,
            summary=bundle.summary,
            manifest=bundle.manifest,
            metadata_source="legacy_backfill",
        )
        drifted = replace(
            original,
            run_name="drifted-name",
            summary_available=False,
            artifact_fingerprint=None,
            last_synced_at=None,
        )
        self.repository.upsert_run_metadata(drifted)

        result = backfill_research_run_metadata(
            root_dir=self.output_dir,
            repository=self.repository,
        )

        self.assertEqual(result.inserted_count, 0)
        self.assertEqual(result.updated_count, 1)
        repaired = self.repository.get_run_metadata(self.run_id)
        self.assertIsNotNone(repaired)
        assert repaired is not None
        self.assertEqual(repaired.run_name, bundle.summary.run_name)
        self.assertTrue(repaired.summary_available)
        self.assertIsNotNone(repaired.artifact_fingerprint)

    def test_report_surfaces_orphaned_db_rows_and_backfill_completeness(self) -> None:
        backfill_research_run_metadata(
            root_dir=self.output_dir,
            repository=self.repository,
        )
        original = self.repository.get_run_metadata(self.run_id)
        self.assertIsNotNone(original)
        assert original is not None
        self.repository.upsert_run_metadata(
            replace(
                original,
                run_id="orphaned-run",
                run_name="orphaned-run",
                summary_path="orphaned-run/summary.json",
                detail_path="orphaned-run/detail.json",
                manifest_path="orphaned-run/manifest.json",
                artifact_fingerprint="orphaned-fingerprint",
            )
        )

        report = report_research_run_metadata_transition(
            root_dir=self.output_dir,
            repository=self.repository,
        )

        self.assertEqual(report.artifact_runs, 1)
        self.assertEqual(report.db_rows, 2)
        self.assertEqual(report.db_backed_runs, 1)
        self.assertEqual(report.orphaned_db_rows, 1)
        self.assertTrue(report.backfill_complete)

    def test_backfill_skips_malformed_summary_without_overwriting_existing_db_row(self) -> None:
        backfill_research_run_metadata(
            root_dir=self.output_dir,
            repository=self.repository,
        )
        summary_path = self.output_dir / self.run_id / "summary.json"
        summary_path.write_text("{bad-json", encoding="utf-8")

        result = backfill_research_run_metadata(
            root_dir=self.output_dir,
            repository=self.repository,
        )
        report = report_research_run_metadata_transition(
            root_dir=self.output_dir,
            repository=self.repository,
        )

        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(report.malformed_runs, 1)
        loaded = self.repository.get_run_metadata(self.run_id)
        self.assertIsNotNone(loaded)
