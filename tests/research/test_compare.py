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
from ml_data import DirectionLabelSpec, FutureReturnLabelSpec  # noqa: E402
from modeling import ModelFamily, ModelSpec, TaskType  # noqa: E402
from persistence import Base, SQLAlchemyResearchRunMetadataRepository, create_database_manager  # noqa: E402
from research import (  # noqa: E402
    InlineCandleSource,
    MLWorkflowSpec,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    StrategyWorkflowSpec,
    compare_saved_runs,
)


def make_candles(count: int = 260) -> tuple[Candle, ...]:
    rows: list[Candle] = []
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(count):
        close = price + (0.1 if i % 3 else -0.04)
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


class CompareTests(unittest.TestCase):
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
        self.candles = InlineCandleSource(candles=make_candles())

    def tearDown(self) -> None:
        self.manager.engine.dispose()
        self.tempdir.cleanup()

    def _run_strategy(self, run_name: str) -> str:
        artifact = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
                ),
                run_config=ResearchRunConfig(
                    run_name=run_name,
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        return artifact.run_id

    def _run_ml(self, run_name: str) -> str:
        return self._run_ml_with_task_type(run_name=run_name, task_type=TaskType.CLASSIFICATION)

    def _run_ml_with_task_type(self, *, run_name: str, task_type: TaskType) -> str:
        if task_type == TaskType.CLASSIFICATION:
            label_specs = (
                FutureReturnLabelSpec(horizon_bars=3, name="ret_h3"),
                DirectionLabelSpec(horizon_bars=3, threshold=0.0, name="dir_h3"),
            )
            target_label = "dir_h3"
            model_specs = (
                ModelSpec(model_id="dummy_cls", family=ModelFamily.DUMMY_CLASSIFIER),
            )
        else:
            label_specs = (FutureReturnLabelSpec(horizon_bars=3, name="ret_h3"),)
            target_label = "ret_h3"
            model_specs = (
                ModelSpec(model_id="dummy_reg", family=ModelFamily.DUMMY_REGRESSOR),
            )
        artifact = self.runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.ML_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                ml_spec=MLWorkflowSpec(
                    task_type=task_type,
                    label_specs=label_specs,
                    target_label=target_label,
                    model_specs=model_specs,
                ),
                run_config=ResearchRunConfig(
                    run_name=run_name,
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        return artifact.run_id

    def test_compare_strategy_runs(self) -> None:
        run_a = self._run_strategy("strategy-a")
        run_b = self._run_strategy("strategy-b")
        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[run_a, run_b],
            mode="strategy",
        )
        self.assertEqual(result.mode, "strategy")
        self.assertEqual(len(result.rows), 2)
        self.assertGreaterEqual(len(result.cards), 1)

    def test_compare_ml_runs(self) -> None:
        run_a = self._run_ml("ml-a")
        run_b = self._run_ml("ml-b")
        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[run_a, run_b],
            mode="ml",
        )
        self.assertEqual(result.mode, "ml")
        self.assertEqual(len(result.rows), 2)
        self.assertGreaterEqual(len(result.cards), 1)

    def test_mixed_compare_rejected(self) -> None:
        run_strategy = self._run_strategy("strategy-only")
        run_ml = self._run_ml("ml-only")
        with self.assertRaises(ValueError):
            compare_saved_runs(
                root_dir=Path(self.output_dir),
                run_ids=[run_strategy, run_ml],
                mode="auto",
            )

    def test_strategy_compare_tolerates_missing_detail(self) -> None:
        run_a = self._run_strategy("strategy-a")
        run_b = self._run_strategy("strategy-b")
        (Path(self.output_dir) / run_a / "detail.json").unlink()

        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[run_a, run_b],
            mode="strategy",
        )
        self.assertEqual(result.mode, "strategy")
        self.assertEqual(len(result.rows), 2)

    def test_ml_compare_tolerates_malformed_detail(self) -> None:
        run_a = self._run_ml("ml-a")
        run_b = self._run_ml("ml-b")
        (Path(self.output_dir) / run_a / "detail.json").write_text("{bad-json", encoding="utf-8")

        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[run_a, run_b],
            mode="ml",
        )
        self.assertEqual(result.mode, "ml")
        self.assertEqual(len(result.rows), 2)

    def test_ml_compare_task_type_mismatch_rejected(self) -> None:
        run_cls = self._run_ml_with_task_type(run_name="ml-cls", task_type=TaskType.CLASSIFICATION)
        run_reg = self._run_ml_with_task_type(run_name="ml-reg", task_type=TaskType.REGRESSION)
        with self.assertRaises(ValueError):
            compare_saved_runs(
                root_dir=Path(self.output_dir),
                run_ids=[run_cls, run_reg],
                mode="ml",
            )

    def test_strategy_compare_with_db_metadata_and_missing_detail_still_succeeds(self) -> None:
        db_runner = ResearchRunner(metadata_repository=self.metadata_repository)
        artifact_a = db_runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
                ),
                run_config=ResearchRunConfig(
                    run_name="strategy-db-a",
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        artifact_b = db_runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
                ),
                run_config=ResearchRunConfig(
                    run_name="strategy-db-b",
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        (Path(self.output_dir) / artifact_a.run_id / "detail.json").unlink()

        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[artifact_a.run_id, artifact_b.run_id],
            mode="strategy",
            metadata_repository=self.metadata_repository,
        )
        self.assertEqual(result.mode, "strategy")
        self.assertEqual(len(result.rows), 2)

    def test_compare_uses_artifact_summary_when_db_metadata_drifts(self) -> None:
        db_runner = ResearchRunner(metadata_repository=self.metadata_repository)
        artifact_a = db_runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
                ),
                run_config=ResearchRunConfig(
                    run_name="strategy-db-a",
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        artifact_b = db_runner.run(
            ResearchRunRequest(
                workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
                instrument=self.instrument,
                interval=BarInterval.D1,
                candle_source=self.candles,
                strategy_spec=StrategyWorkflowSpec(
                    backtest_config=BacktestConfig(warmup_bars=40, min_signal_confidence=0.05)
                ),
                run_config=ResearchRunConfig(
                    run_name="strategy-db-b",
                    output_dir=self.output_dir,
                    persist_summary=True,
                ),
            )
        )
        record = self.metadata_repository.get_run_metadata(artifact_a.run_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.metadata_repository.upsert_run_metadata(
            replace(
                record,
                run_name="db-drift-name",
                interval="1h",
            )
        )

        result = compare_saved_runs(
            root_dir=Path(self.output_dir),
            run_ids=[artifact_a.run_id, artifact_b.run_id],
            mode="strategy",
            metadata_repository=self.metadata_repository,
        )

        self.assertEqual(result.mode, "strategy")
        row = next(row for row in result.rows if row.run_id == artifact_a.run_id)
        self.assertEqual(row.run_name, "strategy-db-a")
        self.assertEqual(row.interval, "1d")


if __name__ == "__main__":
    unittest.main()
