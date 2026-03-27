"""Minimal demo: run strategy and ML research workflows through ResearchRunner."""

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

from backtesting import BacktestConfig  # noqa: E402
from market_data import AssetClass, BarInterval, Candle, Instrument  # noqa: E402
from ml_data import (  # noqa: E402
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    SplitSpec,
)
from modeling import ModelFamily, ModelSpec, TaskType  # noqa: E402
from research import (  # noqa: E402
    InlineCandleSource,
    MLWorkflowSpec,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    StrategyWorkflowSpec,
)


def synthetic_candles(count: int = 420) -> tuple[Candle, ...]:
    random.seed(17)
    candles: list[Candle] = []
    timestamp = datetime.now(timezone.utc) - timedelta(days=count)
    price = 100.0
    for i in range(count):
        trend = 0.12 if i < int(count * 0.55) else -0.05
        wave = math.sin(i / 13.0) * 0.8
        noise = random.uniform(-0.4, 0.4)
        close = max(1.0, price + trend + wave + noise)
        high = max(price, close) + random.uniform(0.02, 0.35)
        low = min(price, close) - random.uniform(0.02, 0.35)
        candles.append(
            Candle(
                timestamp=timestamp,
                open=price,
                high=high,
                low=low,
                close=close,
                volume=2_500_000 + random.uniform(-200_000, 220_000),
            )
        )
        price = close
        timestamp += timedelta(days=1)
    return tuple(candles)


def print_summary(title: str, run_summary: dict) -> None:  # noqa: ANN001
    print(title)
    print("-" * len(title))
    print(f"run_id={run_summary['run_id']}")
    print(f"workflow={run_summary['workflow_type']} status={run_summary['status']}")
    print(f"steps={[s['step_name'] + ':' + s['status'] for s in run_summary['step_results']]}")
    if "strategy" in run_summary:
        s = run_summary["strategy"]
        print(
            f"strategy={s['strategy_id']} trades={s['total_trades']} "
            f"return%={s['total_return_pct']:.2f} max_dd%={s['max_drawdown_pct']:.2f}"
        )
    if "ml" in run_summary:
        m = run_summary["ml"]
        print(
            f"target={m['target_label']} best_model={m['best_model_id']} "
            f"val_{m['primary_metric_name']}={m['best_validation_value']}"
        )
    print()


def main() -> None:
    instrument = Instrument(symbol="AAPL", asset_class=AssetClass.STOCK)
    candles = synthetic_candles()
    runner = ResearchRunner()

    strategy_run = runner.run(
        ResearchRunRequest(
            workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
            instrument=instrument,
            interval=BarInterval.D1,
            candle_source=InlineCandleSource(candles=candles),
            strategy_spec=StrategyWorkflowSpec(
                backtest_config=BacktestConfig(
                    initial_capital=100_000.0,
                    warmup_bars=80,
                    allow_short=True,
                    allow_flip=True,
                    min_signal_confidence=0.10,
                    position_notional_fraction=1.0,
                )
            ),
            run_config=ResearchRunConfig(run_name="strategy-demo"),
        )
    )

    ml_run = runner.run(
        ResearchRunRequest(
            workflow_type=ResearchWorkflowType.ML_RESEARCH,
            instrument=instrument,
            interval=BarInterval.D1,
            candle_source=InlineCandleSource(candles=candles),
            ml_spec=MLWorkflowSpec(
                feature_spec=FeatureSpec(
                    return_windows=(1, 3, 5),
                    log_return_windows=(1, 3),
                    volatility_windows=(5, 20),
                    momentum_windows=(3, 10),
                    sma_windows=(10, 20),
                    sma_crossover_pairs=((10, 20),),
                    atr_windows=(14,),
                    zscore_windows=(20,),
                    include_volume_features=True,
                ),
                label_specs=(
                    FutureReturnLabelSpec(horizon_bars=5, name="ret_h5"),
                    DirectionLabelSpec(horizon_bars=5, threshold=0.0, name="dir_h5"),
                ),
                split_spec=SplitSpec(train_fraction=0.70, validation_fraction=0.15, test_fraction=0.15, gap_bars=1),
                task_type=TaskType.CLASSIFICATION,
                target_label="dir_h5",
                model_specs=(ModelSpec(model_id="dummy_cls", family=ModelFamily.DUMMY_CLASSIFIER),),
            ),
            run_config=ResearchRunConfig(run_name="ml-demo"),
        )
    )

    print_summary("Strategy Research Run", strategy_run.to_summary_dict())
    print_summary("ML Research Run", ml_run.to_summary_dict())


if __name__ == "__main__":
    main()

