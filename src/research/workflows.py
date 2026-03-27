"""Composable workflow helpers for research orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from backtesting import BacktestInput, BacktestResult, BacktestSimulator
from diagnostics import DiagnosticsReport, build_report_from_backtest
from market_data import Candle, HistoricalCandleRequest, Instrument
from market_data.contracts import BarInterval
from market_data.service import MarketDataService
from ml_data import MLDatasetArtifact, MLDatasetRequest, build_ml_dataset
from modeling import TrainingRequest, TrainingRunArtifact, train_and_evaluate
from strategy_engine import TechnicalRuleStrategy
from strategy_engine.strategies.base import Strategy

from .contracts import (
    InlineCandleSource,
    MLWorkflowSpec,
    MarketDataFetchSource,
    StrategyWorkflowSpec,
)
from .validation import resolve_ml_target_label


def resolve_candles(
    *,
    candle_source: InlineCandleSource | MarketDataFetchSource,
    instrument: Instrument,
    interval: BarInterval,
    market_data_service: MarketDataService | None,
) -> tuple[tuple[Candle, ...], Mapping[str, Any]]:
    if isinstance(candle_source, InlineCandleSource):
        candles = tuple(sorted(candle_source.candles, key=lambda c: c.timestamp))
        return candles, {"source_type": "inline_candles", "candle_count": len(candles)}

    if market_data_service is None:
        raise ValueError(
            "MARKET_DATA_FETCH candle source requires ResearchRunner(market_data_service=...)"
        )
    response = market_data_service.fetch_historical_candles(
        candle_source.provider_name,
        HistoricalCandleRequest(
            instrument=instrument,
            interval=interval,
            start=candle_source.start,
            end=candle_source.end,
            limit=candle_source.limit,
        ),
    )
    candles = tuple(sorted(response.candles, key=lambda c: c.timestamp))
    return candles, {
        "source_type": "market_data_fetch",
        "provider": response.provider,
        "candle_count": len(candles),
        "provider_metadata": dict(response.metadata),
    }


def build_strategy(spec: StrategyWorkflowSpec) -> Strategy:
    if spec.strategy_id == "technical_rule_v1":
        return TechnicalRuleStrategy(parameter_set=spec.parameter_set)
    raise ValueError(f"Unsupported strategy_id: {spec.strategy_id}")


def run_strategy_backtest(
    *,
    candles: tuple[Candle, ...],
    instrument: Instrument,
    interval: BarInterval,
    strategy_spec: StrategyWorkflowSpec,
) -> tuple[BacktestResult, str]:
    strategy = build_strategy(strategy_spec)
    simulator = BacktestSimulator()
    result = simulator.run(
        backtest_input=BacktestInput(
            instrument=instrument,
            interval=interval,
            candles=candles,
        ),
        strategy=strategy,
        config=strategy_spec.backtest_config,
    )
    return result, strategy.name


def run_strategy_diagnostics(
    *,
    backtest_result: BacktestResult,
    strategy_spec: StrategyWorkflowSpec,
    run_id: str,
    run_name: str,
) -> DiagnosticsReport:
    return build_report_from_backtest(
        backtest_result,
        config=strategy_spec.diagnostics_config,
        run_id=run_id,
        run_name=run_name,
    )


def run_ml_dataset_build(
    *,
    candles: tuple[Candle, ...],
    instrument: Instrument,
    interval: BarInterval,
    ml_spec: MLWorkflowSpec,
) -> MLDatasetArtifact:
    request = MLDatasetRequest(
        instrument=instrument,
        interval=interval,
        candles=candles,
        feature_spec=ml_spec.feature_spec,
        label_specs=ml_spec.label_specs,
        split_spec=ml_spec.split_spec,
        missing_volume_policy=ml_spec.missing_volume_policy,
        missing_value_policy=ml_spec.missing_value_policy,
    )
    return build_ml_dataset(request)


def run_model_training(
    *,
    dataset: MLDatasetArtifact,
    ml_spec: MLWorkflowSpec,
    run_seed: int,
) -> tuple[TrainingRunArtifact, str]:
    target_label = resolve_ml_target_label(ml_spec)
    training_config = replace(ml_spec.training_config, random_seed=run_seed)
    training_request = TrainingRequest(
        dataset=dataset,
        target_label=target_label,
        task_type=ml_spec.task_type,
        model_specs=ml_spec.model_specs,
        config=training_config,
    )
    return train_and_evaluate(training_request), target_label
