"""Minimal demo: candles -> strategy -> backtest simulation result."""

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
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from strategy_engine import (  # noqa: E402
    TechnicalRuleParameterSet,
    TechnicalRuleStrategy,
    TechnicalRuleThresholds,
)


def synthetic_candles(count: int = 420) -> tuple[Candle, ...]:
    random.seed(12)
    out: list[Candle] = []
    ts = datetime.now(timezone.utc) - timedelta(minutes=count)
    price = 100.0

    for i in range(count):
        wave = math.sin(i / 11.0) * 0.45
        drift = 0.004 if i < (count * 0.55) else -0.003
        shock = random.uniform(-0.18, 0.18)
        close = max(1.0, price + drift + wave + shock)
        high = max(price, close) + random.uniform(0.01, 0.12)
        low = min(price, close) - random.uniform(0.01, 0.12)
        volume = 1000.0 + random.uniform(-300.0, 350.0)
        out.append(
            Candle(
                timestamp=ts,
                open=price,
                high=high,
                low=low,
                close=close,
                volume=max(1.0, volume),
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

    result = simulator.run(
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
            risk_exits=RiskExitConfig(
                stop_loss_fraction=0.02,
                take_profit_fraction=0.04,
            ),
        ),
    )

    s = result.summary
    print("Summary")
    print("-------")
    print(f"Final equity: {s.final_equity:.2f}")
    print(f"Total net pnl: {s.total_net_pnl:.2f}")
    print(f"Total fees: {s.total_fees:.2f}")
    print(f"Total return %: {s.total_return_pct:.2f}")
    print(f"Max drawdown %: {s.max_drawdown_pct:.2f}")
    print(f"Trades: {s.total_trades}")
    print(f"Win rate %: {s.win_rate_pct:.2f}")
    print(f"Sharpe: {s.sharpe_ratio}")
    print("Diagnostics:", result.diagnostics)
    if result.trades:
        first = result.trades[0]
        print()
        print("First trade")
        print("-----------")
        print(
            f"{first.direction.value} {first.entry_time.isoformat()} -> "
            f"{first.exit_time.isoformat()} net_pnl={first.net_pnl:.2f} "
            f"return%={first.return_pct:.4f} reason={first.exit_reason.value}"
        )


if __name__ == "__main__":
    main()
