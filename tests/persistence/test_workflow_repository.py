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
    SQLAlchemyWorkflowPersistenceRepository,
    create_database_manager,
)
from persistence.workflow_objects import (  # noqa: E402
    SAVED_CONFIG_SCHEMA_VERSION,
    SavedResearchConfigRecord,
)


def sample_strategy_payload(symbol: str = "AAPL") -> dict:
    return {
        "instrument": {"symbol": symbol, "asset_class": "stock"},
        "interval": "1d",
        "candle_source": {"source_type": "inline_sample", "inline_bars": 220},
        "strategy_spec": {
            "strategy_id": "technical_rule_v1",
            "backtest_config": {"warmup_bars": 80, "min_signal_confidence": 0.1},
        },
        "run_config": {
            "run_name": "strategy-aapl-template",
            "strict_failures": True,
            "persist_summary": False,
            "metadata": {},
        },
    }


def make_saved_config(config_id: str, *, config_type: str = "strategy") -> SavedResearchConfigRecord:
    when = datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc)
    return SavedResearchConfigRecord(
        id=config_id,
        config_type=config_type,
        name=f"{config_type}-template",
        description="test",
        config_schema_version=SAVED_CONFIG_SCHEMA_VERSION,
        payload_json=sample_strategy_payload("AAPL" if config_type == "strategy" else "MSFT"),
        instrument_symbol="AAPL" if config_type == "strategy" else "MSFT",
        asset_class="stock",
        interval="1d",
        created_at=when,
        updated_at=when,
        last_used_at=None,
    )


class WorkflowRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "workflow.sqlite3"
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
        self.repository = SQLAlchemyWorkflowPersistenceRepository(
            session_factory=manager.session_factory
        )

    def tearDown(self) -> None:
        self.manager.engine.dispose()
        self.tempdir.cleanup()

    def test_saved_config_create_update_get_and_delete(self) -> None:
        created = self.repository.create_saved_config(make_saved_config("strategy_cfg_001"))
        self.assertEqual(created.id, "strategy_cfg_001")

        loaded = self.repository.get_saved_config("strategy_cfg_001")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.name, "strategy-template")

        updated = self.repository.update_saved_config(
            SavedResearchConfigRecord(
                **{
                    **loaded.__dict__,
                    "name": "strategy-template-v2",
                }
            )
        )
        self.assertEqual(updated.name, "strategy-template-v2")

        marked = self.repository.mark_saved_config_used("strategy_cfg_001")
        self.assertIsNotNone(marked)
        assert marked is not None
        self.assertIsNotNone(marked.last_used_at)

        self.assertTrue(self.repository.delete_saved_config("strategy_cfg_001"))
        self.assertIsNone(self.repository.get_saved_config("strategy_cfg_001"))

    def test_saved_config_listing_filters_by_type(self) -> None:
        self.repository.create_saved_config(make_saved_config("strategy_cfg_001", config_type="strategy"))
        self.repository.create_saved_config(make_saved_config("ml_cfg_001", config_type="ml"))

        strategy_items = self.repository.list_saved_configs(config_type="strategy")
        ml_items = self.repository.list_saved_configs(config_type="ml")

        self.assertEqual([item.id for item in strategy_items], ["strategy_cfg_001"])
        self.assertEqual([item.id for item in ml_items], ["ml_cfg_001"])

    def test_watchlist_upsert_delete_and_recent_touches_dedupe(self) -> None:
        first = self.repository.upsert_watchlist_item(
            symbol="AAPL",
            asset_class="stock",
            source_context="strategy_page",
        )
        second = self.repository.upsert_watchlist_item(
            symbol="AAPL",
            asset_class="stock",
            source_context="ml_page",
        )
        self.assertEqual(first.id, second.id)
        watchlist = self.repository.list_watchlist_items()
        self.assertEqual(len(watchlist), 1)
        self.assertEqual(watchlist[0].source_context, "ml_page")
        self.assertTrue(
            self.repository.delete_watchlist_item(asset_class="stock", symbol="AAPL")
        )

        recent_first = self.repository.touch_recent_asset(
            symbol="AAPL",
            asset_class="stock",
            source_context="strategy_submit",
        )
        recent_second = self.repository.touch_recent_asset(
            symbol="AAPL",
            asset_class="stock",
            source_context="ml_submit",
        )
        self.assertEqual(recent_first.id, recent_second.id)
        recent_assets = self.repository.list_recent_assets()
        self.assertEqual(len(recent_assets), 1)
        self.assertEqual(recent_assets[0].source_context, "ml_submit")

    def test_recent_compare_sets_dedupe_by_fingerprint(self) -> None:
        first = self.repository.touch_recent_compare_set(
            compare_mode="strategy",
            run_ids=["run-001", "run-002"],
        )
        second = self.repository.touch_recent_compare_set(
            compare_mode="strategy",
            run_ids=["run-001", "run-002"],
        )
        third = self.repository.touch_recent_compare_set(
            compare_mode="strategy",
            run_ids=["run-002", "run-001"],
        )

        self.assertEqual(first.id, second.id)
        self.assertNotEqual(first.id, third.id)
        recent_sets = self.repository.list_recent_compare_sets()
        self.assertEqual(len(recent_sets), 2)


if __name__ == "__main__":
    unittest.main()
