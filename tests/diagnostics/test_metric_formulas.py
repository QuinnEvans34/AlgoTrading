import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from diagnostics import (  # noqa: E402
    DiagnosticEquityPoint,
    DiagnosticTrade,
    DiagnosticsConfig,
    DiagnosticsInput,
    annualized_return_pct,
    build_report,
)
from market_data import AssetClass, BarInterval, Instrument  # noqa: E402


class DiagnosticsMetricFormulaTests(unittest.TestCase):
    def test_annualized_return_helper(self) -> None:
        result = annualized_return_pct(
            initial_capital=100.0,
            final_equity=121.0,
            periods=252,
            bars_per_year=252,
            annualize_returns=True,
            min_periods_for_annualization=2,
            min_years_for_annualization=1.0 / 12.0,
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertAlmostEqual(result, 21.0, places=6)

    def test_hand_checked_trade_and_drawdown_metrics(self) -> None:
        instrument = Instrument(symbol="QQQ", asset_class=AssetClass.STOCK)
        t0 = datetime(2026, 4, 1, tzinfo=timezone.utc)
        t1 = t0 + timedelta(days=1)
        t2 = t1 + timedelta(days=1)
        t3 = t2 + timedelta(days=1)

        diagnostics_input = DiagnosticsInput(
            run_id="formula-check",
            run_name="Formula Check",
            instrument=instrument,
            interval=BarInterval.D1,
            initial_capital=1000.0,
            trades=(
                DiagnosticTrade(
                    direction="long",
                    entry_time=t0,
                    exit_time=t1,
                    entry_price=100.0,
                    exit_price=105.0,
                    units=10.0,
                    gross_pnl=52.0,
                    net_pnl=50.0,
                    return_pct=5.0,
                    bars_held=1,
                    entry_commission=1.0,
                    exit_commission=1.0,
                    exit_reason="signal_flip",
                ),
                DiagnosticTrade(
                    direction="short",
                    entry_time=t2,
                    exit_time=t3,
                    entry_price=100.0,
                    exit_price=103.0,
                    units=10.0,
                    gross_pnl=-28.0,
                    net_pnl=-30.0,
                    return_pct=-3.0,
                    bars_held=1,
                    entry_commission=1.0,
                    exit_commission=1.0,
                    exit_reason="end_of_data",
                ),
            ),
            equity_curve=(
                DiagnosticEquityPoint(
                    timestamp=t0,
                    equity=1000.0,
                    cash=1000.0,
                    unrealized_pnl=0.0,
                ),
                DiagnosticEquityPoint(
                    timestamp=t1,
                    equity=1080.0,
                    cash=1080.0,
                    unrealized_pnl=0.0,
                ),
                DiagnosticEquityPoint(
                    timestamp=t2,
                    equity=990.0,
                    cash=990.0,
                    unrealized_pnl=0.0,
                ),
                DiagnosticEquityPoint(
                    timestamp=t3,
                    equity=1020.0,
                    cash=1020.0,
                    unrealized_pnl=0.0,
                ),
            ),
        )

        report = build_report(
            diagnostics_input,
            config=DiagnosticsConfig(annualize_returns=False),
        )

        self.assertAlmostEqual(report.performance.final_equity, 1020.0, places=6)
        self.assertAlmostEqual(report.performance.total_return_pct, 2.0, places=6)
        self.assertAlmostEqual(report.performance.total_net_pnl, 20.0, places=6)
        self.assertAlmostEqual(report.performance.total_commissions, 4.0, places=6)

        self.assertEqual(report.trade_analysis.trade_count, 2)
        self.assertAlmostEqual(report.trade_analysis.win_rate_pct or 0.0, 50.0, places=6)
        self.assertAlmostEqual(report.trade_analysis.expectancy_net_pnl or 0.0, 10.0, places=6)
        self.assertAlmostEqual(report.trade_analysis.profit_factor or 0.0, 50.0 / 30.0, places=6)
        self.assertAlmostEqual(report.trade_analysis.payoff_ratio or 0.0, 50.0 / 30.0, places=6)

        self.assertAlmostEqual(report.risk.max_drawdown_pct, (90.0 / 1080.0) * 100.0, places=6)
        self.assertGreaterEqual(report.risk.max_drawdown_duration_bars, 1)
        self.assertEqual(len(report.series.return_series), 3)
        self.assertEqual(len(report.series.trade_net_pnls), 2)


if __name__ == "__main__":
    unittest.main()
