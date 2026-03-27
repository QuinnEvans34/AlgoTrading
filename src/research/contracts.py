"""Typed contracts for research orchestration workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from backtesting import BacktestConfig
from diagnostics import DiagnosticsConfig
from market_data import BarInterval, Candle, Instrument
from ml_data import (
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    LabelSpec,
    MissingValuePolicy,
    MissingVolumePolicy,
    SplitSpec,
)
from modeling import ModelSpec, TaskType, TrainingConfig
from strategy_engine import TechnicalRuleParameterSet


class ResearchWorkflowType(str, Enum):
    STRATEGY_RESEARCH = "strategy_research"
    ML_RESEARCH = "ml_research"
    HYBRID_RESEARCH = "hybrid_research"


class CandleSourceType(str, Enum):
    INLINE_CANDLES = "inline_candles"
    MARKET_DATA_FETCH = "market_data_fetch"


class StepStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class RunStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


@dataclass(frozen=True)
class InlineCandleSource:
    candles: tuple[Candle, ...]


@dataclass(frozen=True)
class MarketDataFetchSource:
    provider_name: str
    start: datetime
    end: datetime
    limit: int | None = None


CandleSourceSpec = InlineCandleSource | MarketDataFetchSource


@dataclass(frozen=True)
class StrategyWorkflowSpec:
    strategy_id: str = "technical_rule_v1"
    parameter_set: TechnicalRuleParameterSet | None = None
    backtest_config: BacktestConfig = field(default_factory=BacktestConfig)
    diagnostics_config: DiagnosticsConfig | None = None


@dataclass(frozen=True)
class MLWorkflowSpec:
    feature_spec: FeatureSpec = field(default_factory=FeatureSpec)
    label_specs: tuple[LabelSpec, ...] = field(
        default_factory=lambda: (FutureReturnLabelSpec(horizon_bars=1),)
    )
    split_spec: SplitSpec | None = None
    missing_volume_policy: MissingVolumePolicy = MissingVolumePolicy.SKIP_VOLUME_FEATURES
    missing_value_policy: MissingValuePolicy = MissingValuePolicy.DROP_ROW
    task_type: TaskType = TaskType.REGRESSION
    target_label: str | None = None
    model_specs: tuple[ModelSpec, ...] = ()
    training_config: TrainingConfig = field(default_factory=TrainingConfig)


@dataclass(frozen=True)
class ResearchRunConfig:
    run_id: str | None = None
    run_name: str | None = None
    random_seed: int = 42
    strict_failures: bool = True
    persist_summary: bool = False
    output_dir: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchRunRequest:
    workflow_type: ResearchWorkflowType
    instrument: Instrument
    interval: BarInterval
    candle_source: CandleSourceSpec
    strategy_spec: StrategyWorkflowSpec | None = None
    ml_spec: MLWorkflowSpec | None = None
    run_config: ResearchRunConfig = field(default_factory=ResearchRunConfig)


@dataclass(frozen=True)
class ResearchStepResult:
    step_name: str
    status: StepStatus
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    error_type: str | None = None
    error_message: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

