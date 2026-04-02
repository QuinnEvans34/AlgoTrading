import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from config import DatabaseSettings  # noqa: E402
from persistence import (  # noqa: E402
    Base,
    SQLAlchemyResearchRunMetadataRepository,
    create_database_manager,
)
from persistence.research_runs import ResearchRunMetadataQuery, ResearchRunMetadataRecord  # noqa: E402


def make_record(
    run_id: str,
    *,
    workflow_type: str = "strategy_research",
    status: str = "success",
    symbol: str = "AAPL",
    started_at: datetime | None = None,
) -> ResearchRunMetadataRecord:
    when = started_at or datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc)
    return ResearchRunMetadataRecord(
        run_id=run_id,
        run_name=run_id,
        workflow_type=workflow_type,
        status=status,
        started_at=when,
        ended_at=when,
        duration_ms=100,
        instrument_symbol=symbol,
        asset_class="stock",
        interval="1d",
        candle_count=220,
        candle_source_type="inline_candles",
        has_strategy=workflow_type != "ml_research",
        has_ml=workflow_type == "ml_research",
        strategy_id="technical_rule_v1" if workflow_type != "ml_research" else None,
        total_trades=12 if workflow_type != "ml_research" else None,
        total_return_pct=10.5 if workflow_type != "ml_research" else None,
        total_net_pnl=1000.0 if workflow_type != "ml_research" else None,
        max_drawdown_pct=-3.0 if workflow_type != "ml_research" else None,
        sharpe_ratio=1.1 if workflow_type != "ml_research" else None,
        ml_task_type="classification" if workflow_type == "ml_research" else None,
        ml_target_label="dir_h5" if workflow_type == "ml_research" else None,
        ml_best_model_id="dummy_cls" if workflow_type == "ml_research" else None,
        ml_primary_metric_name="accuracy" if workflow_type == "ml_research" else None,
        ml_best_validation_value=0.61 if workflow_type == "ml_research" else None,
        ml_best_test_value=0.59 if workflow_type == "ml_research" else None,
        ml_model_count_executed=1 if workflow_type == "ml_research" else None,
        ml_model_count_skipped=0 if workflow_type == "ml_research" else None,
        ml_warning_count=0 if workflow_type == "ml_research" else None,
        summary_path=f"{run_id}/summary.json",
        detail_path=f"{run_id}/detail.json",
        manifest_path=f"{run_id}/manifest.json",
        metadata_schema_version=1,
        artifact_schema_version=1,
        metadata_source="dual_write",
        manifest_synthetic=False,
        summary_available=True,
        detail_available=True,
        created_at=when,
        updated_at=when,
        artifact_fingerprint=f"fp-{run_id}",
        last_synced_at=when,
    )


class ResearchRunMetadataRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
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

    def test_upsert_and_get_roundtrip(self) -> None:
        record = make_record("run-001")
        self.repository.upsert_run_metadata(record)

        loaded = self.repository.get_run_metadata("run-001")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.run_id, "run-001")
        self.assertEqual(loaded.instrument_symbol, "AAPL")

    def test_list_filters_sort_and_search(self) -> None:
        self.repository.upsert_run_metadata(make_record("run-001", symbol="AAPL"))
        self.repository.upsert_run_metadata(
            make_record(
                "run-002",
                workflow_type="ml_research",
                symbol="MSFT",
                started_at=datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
            )
        )

        filtered = self.repository.list_run_metadata(
            ResearchRunMetadataQuery(workflow_type="ml_research")
        )
        self.assertEqual(filtered.total, 1)
        self.assertEqual(filtered.items[0].run_id, "run-002")

        searched = self.repository.list_run_metadata(
            ResearchRunMetadataQuery(search="msft")
        )
        self.assertEqual(searched.total, 1)
        self.assertEqual(searched.items[0].run_id, "run-002")

        paged = self.repository.list_run_metadata(
            ResearchRunMetadataQuery(limit=1, offset=0, sort="started_desc")
        )
        self.assertEqual(paged.total, 2)
        self.assertEqual(len(paged.items), 1)
        self.assertEqual(paged.items[0].run_id, "run-002")

    def test_missing_row_returns_none(self) -> None:
        self.assertIsNone(self.repository.get_run_metadata("does-not-exist"))
