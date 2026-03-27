import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import BacktestConfig  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from research import (  # noqa: E402
    InlineCandleSource,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    RunStatus,
    StrategyWorkflowSpec,
    list_run_history,
)


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

    @staticmethod
    def _query():
        from research import RunHistoryQuery

        return RunHistoryQuery(limit=100, offset=0)


if __name__ == "__main__":
    unittest.main()
