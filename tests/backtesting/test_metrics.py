import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting.contracts import (  # noqa: E402
    EquityPoint,
    ExitReason,
    PositionDirection,
    Trade,
)
from backtesting.metrics import build_summary  # noqa: E402
from market_data import AssetClass, Instrument  # noqa: E402


class MetricsTests(unittest.TestCase):
    def test_summary_fields(self) -> None:
        instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
        ts = datetime.now(timezone.utc)

        trades = [
            Trade(
                instrument=instrument,
                direction=PositionDirection.LONG,
                entry_time=ts,
                exit_time=ts,
                entry_price=100.0,
                exit_price=103.0,
                units=10.0,
                gross_pnl=30.0,
                net_pnl=28.0,
                return_pct=2.8,
                bars_held=5,
                exit_reason=ExitReason.SIGNAL_FLIP,
                entry_commission=1.0,
                exit_commission=1.0,
            ),
            Trade(
                instrument=instrument,
                direction=PositionDirection.SHORT,
                entry_time=ts,
                exit_time=ts,
                entry_price=105.0,
                exit_price=108.0,
                units=10.0,
                gross_pnl=-30.0,
                net_pnl=-32.0,
                return_pct=-3.2,
                bars_held=4,
                exit_reason=ExitReason.END_OF_DATA,
                entry_commission=1.0,
                exit_commission=1.0,
            ),
        ]

        curve = [
            EquityPoint(timestamp=ts, equity=1000.0, cash=1000.0, unrealized_pnl=0.0, drawdown_pct=0.0),
            EquityPoint(timestamp=ts, equity=1030.0, cash=1030.0, unrealized_pnl=0.0, drawdown_pct=0.0),
            EquityPoint(timestamp=ts, equity=998.0, cash=998.0, unrealized_pnl=0.0, drawdown_pct=3.1067961165),
        ]

        summary = build_summary(
            initial_capital=1000.0,
            trades=trades,
            equity_curve=curve,
            bars_per_year=252,
        )

        self.assertAlmostEqual(summary.final_equity, 998.0, places=6)
        self.assertAlmostEqual(summary.total_gross_pnl, 0.0, places=6)
        self.assertAlmostEqual(summary.total_net_pnl, -4.0, places=6)
        self.assertAlmostEqual(summary.total_fees, 4.0, places=6)
        self.assertAlmostEqual(summary.max_drawdown_pct, 3.1067961165, places=6)
        self.assertEqual(summary.total_trades, 2)
        self.assertAlmostEqual(summary.win_rate_pct, 50.0, places=6)
        self.assertAlmostEqual(summary.avg_trade_net_pnl, -2.0, places=6)
        self.assertIsNotNone(summary.profit_factor)


if __name__ == "__main__":
    unittest.main()
