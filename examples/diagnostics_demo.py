"""Minimal diagnostics demo: backtest result -> diagnostics report."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from backtesting import (  # noqa: E402
    BacktestConfig,
    BacktestInput,
    BacktestSimulator,
    CompositeCommissionModel,
    FillModel,
    FixedBpsSlippageModel,
    FixedBpsSpreadModel,
    RiskExitConfig,
)
from diagnostics import build_report_from_backtest  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from strategy_engine import (  # noqa: E402
    TechnicalRuleParameterSet,
    TechnicalRuleStrategy,
    TechnicalRuleThresholds,
)


def synthetic_candles(count: int = 420) -> tuple[Candle, ...]:
    random.seed(21)
    out: list[Candle] = []
    ts = datetime.now(timezone.utc) - timedelta(minutes=count)
    price = 100.0
    for i in range(count):
        wave = math.sin(i / 10.0) * 0.38
        drift = 0.004 if i < (count * 0.50) else -0.0025
        shock = random.uniform(-0.15, 0.15)
        close = max(1.0, price + drift + wave + shock)
        high = max(price, close) + random.uniform(0.01, 0.10)
        low = min(price, close) - random.uniform(0.01, 0.10)
        volume = max(1.0, 1000.0 + random.uniform(-250.0, 250.0))
        out.append(
            Candle(
                timestamp=ts,
                open=price,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )
        price = close
        ts += timedelta(minutes=1)
    return tuple(out)


def main() -> None:
    instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
    candles = synthetic_candles()

    relaxed = TechnicalRuleThresholds(
        min_confidence=0.10,
        rsi_z_threshold=0.45,
        adx_floor=1.0,
        volatility_min=0.0,
        volatility_max=9.0,
        stoch_lower=40.0,
        stoch_upper=60.0,
        macd_noise_factor=0.2,
    )
    params = TechnicalRuleParameterSet(
        default_thresholds=TechnicalRuleThresholds(),
        by_asset_class=TechnicalRuleParameterSet.multi_asset_defaults().by_asset_class,
        by_symbol={"AAPL": relaxed},
    )
    strategy = TechnicalRuleStrategy(parameter_set=params)

    simulator = BacktestSimulator(
        fill_model=FillModel(
            spread_model=FixedBpsSpreadModel(half_spread_bps=0.5),
            slippage_model=FixedBpsSlippageModel(bps=0.5),
        ),
        commission_model=CompositeCommissionModel(notional_bps=1.0, fixed_fee=0.10),
    )
    backtest_result = simulator.run(
        backtest_input=BacktestInput(
            instrument=instrument,
            interval=BarInterval.M1,
            candles=candles,
        ),
        strategy=strategy,
        config=BacktestConfig(
            initial_capital=100_000.0,
            warmup_bars=80,
            allow_short=True,
            allow_flip=True,
            min_signal_confidence=0.10,
            position_notional_fraction=1.0,
            max_bars_in_position=120,
            risk_exits=RiskExitConfig(stop_loss_fraction=0.02, take_profit_fraction=0.04),
        ),
    )

    report = build_report_from_backtest(
        backtest_result,
        run_id="demo-run-001",
        run_name="AAPL Technical Rule Demo",
    )

    print("Diagnostics Summary")
    print("-------------------")
    print(f"Final equity: {report.performance.final_equity:.2f}")
    print(f"Total return %: {report.performance.total_return_pct:.2f}")
    print(f"Annualized return %: {report.performance.annualized_return_pct}")
    print(f"Trades: {report.trade_analysis.trade_count}")
    print(f"Win rate %: {report.trade_analysis.win_rate_pct}")
    print(f"Profit factor: {report.trade_analysis.profit_factor}")
    print(f"Max drawdown %: {report.risk.max_drawdown_pct:.2f}")
    print(f"Sharpe: {report.risk.sharpe_ratio}")
    print(f"Sortino: {report.risk.sortino_ratio}")
    print(f"Drawdown episodes: {len(report.drawdown_episodes)}")

    if report.trade_analysis.top_losing_trades:
        worst = report.trade_analysis.top_losing_trades[0]
        print()
        print("Worst Trade")
        print("-----------")
        print(
            f"{worst.direction} {worst.entry_time.isoformat()} -> {worst.exit_time.isoformat()} "
            f"net_pnl={worst.net_pnl:.2f} return%={worst.return_pct:.4f} "
            f"bars={worst.bars_held} reason={worst.exit_reason}"
        )


if __name__ == "__main__":
    main()

