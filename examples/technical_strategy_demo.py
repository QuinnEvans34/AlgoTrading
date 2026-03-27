"""Minimal demo: normalized candles in, strategy signal out."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from strategy_engine import (  # noqa: E402
    StrategyEngine,
    StrategyInput,
    TechnicalRuleParameterSet,
    TechnicalRuleStrategy,
    TechnicalRuleThresholds,
)


def synthetic_candles(count: int = 220) -> tuple[Candle, ...]:
    random.seed(55)
    out: list[Candle] = []
    ts = datetime.now(timezone.utc) - timedelta(minutes=count)
    price = 100.0

    for i in range(count):
        if i < 80:
            drift = -0.04
        elif i < 160:
            drift = 0.05
        else:
            drift = -0.01
        shock = random.uniform(-0.2, 0.2)
        close = max(1.0, price + drift + shock)
        high = max(price, close) + random.uniform(0.01, 0.12)
        low = min(price, close) - random.uniform(0.01, 0.12)
        volume = 1000 + random.uniform(-400, 500)
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
        ts += timedelta(minutes=1)
        price = close
    return tuple(out)


def main() -> None:
    instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
    candles = synthetic_candles()

    relaxed = TechnicalRuleThresholds(
        min_confidence=0.05,
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

    strategy = TechnicalRuleStrategy(
        parameter_set=params
    )
    engine = StrategyEngine()
    strategy_input = StrategyInput(
        instrument=instrument,
        interval=BarInterval.M1,
        candles=candles,
    )
    evaluation = engine.evaluate(strategy, strategy_input)

    print(f"Strategy: {evaluation.strategy_name}")
    print(f"Instrument: {evaluation.instrument.symbol} ({evaluation.instrument.asset_class.value})")
    print(f"Candles: {evaluation.candle_count}")
    if evaluation.signal:
        print(
            "Signal:",
            evaluation.signal.direction.value,
            f"confidence={evaluation.signal.confidence:.2f}",
            f"score={evaluation.signal.score:.2f}",
        )
        print("Rationale:", "; ".join(evaluation.signal.rationale))
    else:
        print("Signal: none")
        print("Diagnostics:", evaluation.diagnostics)
    print("Indicators:", evaluation.indicators)


if __name__ == "__main__":
    main()
