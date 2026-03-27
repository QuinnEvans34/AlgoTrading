"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from backtesting import (
    BacktestConfig,
    ExecutionTiming,
    IntrabarExitPolicy,
    RiskExitConfig,
    SizingMode,
)
from diagnostics import DiagnosticsConfig
from market_data import AssetClass, BarInterval
from ml_data import MissingValuePolicy, MissingVolumePolicy
from modeling import ModelFamily, OptionalDependencyPolicy, TaskType
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorDetailSchema(StrictModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class ErrorResponseSchema(StrictModel):
    error: ErrorDetailSchema


class HealthResponseSchema(StrictModel):
    status: str
    service: str
    version: str
    timestamp: datetime


class InstrumentSchema(StrictModel):
    symbol: str
    asset_class: AssetClass
    venue: str | None = None
    quote_currency: str | None = None


class CandleSchema(StrictModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class InlineCandleSourceSchema(StrictModel):
    source_type: Literal["inline_candles"] = "inline_candles"
    candles: list[CandleSchema] = Field(min_length=1)


class MarketDataFetchSourceSchema(StrictModel):
    source_type: Literal["market_data_fetch"] = "market_data_fetch"
    provider_name: str
    start: datetime
    end: datetime
    limit: int | None = Field(default=None, gt=0)


CandleSourceSchema = Annotated[
    InlineCandleSourceSchema | MarketDataFetchSourceSchema,
    Field(discriminator="source_type"),
]


class RiskExitConfigSchema(StrictModel):
    stop_loss_fraction: float | None = None
    take_profit_fraction: float | None = None
    intrabar_exit_policy: IntrabarExitPolicy = IntrabarExitPolicy.ADVERSE_FIRST

    def to_domain(self) -> RiskExitConfig:
        return RiskExitConfig(
            stop_loss_fraction=self.stop_loss_fraction,
            take_profit_fraction=self.take_profit_fraction,
            intrabar_exit_policy=self.intrabar_exit_policy,
        )


class BacktestConfigSchema(StrictModel):
    initial_capital: float = BacktestConfig.initial_capital
    warmup_bars: int = BacktestConfig.warmup_bars
    allow_short: bool = BacktestConfig.allow_short
    allow_flip: bool = BacktestConfig.allow_flip
    close_position_on_end: bool = BacktestConfig.close_position_on_end
    max_bars_in_position: int | None = BacktestConfig.max_bars_in_position
    min_signal_confidence: float = BacktestConfig.min_signal_confidence
    sizing_mode: SizingMode = BacktestConfig.sizing_mode
    position_notional_fraction: float = BacktestConfig.position_notional_fraction
    entry_timing: ExecutionTiming = BacktestConfig.entry_timing
    signal_exit_timing: ExecutionTiming = BacktestConfig.signal_exit_timing
    risk_exits: RiskExitConfigSchema | None = None

    def to_domain(self) -> BacktestConfig:
        return BacktestConfig(
            initial_capital=self.initial_capital,
            warmup_bars=self.warmup_bars,
            allow_short=self.allow_short,
            allow_flip=self.allow_flip,
            close_position_on_end=self.close_position_on_end,
            max_bars_in_position=self.max_bars_in_position,
            min_signal_confidence=self.min_signal_confidence,
            sizing_mode=self.sizing_mode,
            position_notional_fraction=self.position_notional_fraction,
            entry_timing=self.entry_timing,
            signal_exit_timing=self.signal_exit_timing,
            risk_exits=(None if self.risk_exits is None else self.risk_exits.to_domain()),
        )


class DiagnosticsConfigSchema(StrictModel):
    annualize_returns: bool = DiagnosticsConfig.annualize_returns
    annual_risk_free_rate: float = DiagnosticsConfig.annual_risk_free_rate
    min_periods_for_annualization: int = DiagnosticsConfig.min_periods_for_annualization
    min_years_for_annualization: float = DiagnosticsConfig.min_years_for_annualization
    min_periods_for_risk_metrics: int = DiagnosticsConfig.min_periods_for_risk_metrics
    top_trade_annotations: int = DiagnosticsConfig.top_trade_annotations
    max_drawdown_episodes: int = DiagnosticsConfig.max_drawdown_episodes

    def to_domain(self) -> DiagnosticsConfig:
        return DiagnosticsConfig(
            annualize_returns=self.annualize_returns,
            annual_risk_free_rate=self.annual_risk_free_rate,
            min_periods_for_annualization=self.min_periods_for_annualization,
            min_years_for_annualization=self.min_years_for_annualization,
            min_periods_for_risk_metrics=self.min_periods_for_risk_metrics,
            top_trade_annotations=self.top_trade_annotations,
            max_drawdown_episodes=self.max_drawdown_episodes,
        )


class StrategyWorkflowSpecSchema(StrictModel):
    strategy_id: str = "technical_rule_v1"
    backtest_config: BacktestConfigSchema = Field(default_factory=BacktestConfigSchema)
    diagnostics_config: DiagnosticsConfigSchema | None = None


class FeatureSpecSchema(StrictModel):
    return_windows: tuple[int, ...] = (1, 3, 5)
    log_return_windows: tuple[int, ...] = (1, 3, 5)
    volatility_windows: tuple[int, ...] = (5, 20)
    momentum_windows: tuple[int, ...] = (3, 10)
    sma_windows: tuple[int, ...] = (10, 20)
    sma_crossover_pairs: tuple[tuple[int, int], ...] = ((10, 20),)
    atr_windows: tuple[int, ...] = (14,)
    zscore_windows: tuple[int, ...] = (20,)
    include_candle_structure: bool = True
    include_volume_features: bool = True
    volume_zscore_windows: tuple[int, ...] = (10,)


class FutureReturnLabelSpecSchema(StrictModel):
    label_type: Literal["future_return"] = "future_return"
    horizon_bars: int
    name: str | None = None
    price_field: str = "close"


class DirectionLabelSpecSchema(StrictModel):
    label_type: Literal["direction"] = "direction"
    horizon_bars: int
    threshold: float = 0.0
    name: str | None = None
    price_field: str = "close"


LabelSpecSchema = Annotated[
    FutureReturnLabelSpecSchema | DirectionLabelSpecSchema,
    Field(discriminator="label_type"),
]


class SplitSpecSchema(StrictModel):
    train_fraction: float = 0.70
    validation_fraction: float = 0.15
    test_fraction: float = 0.15
    gap_bars: int = 0


class ModelSpecSchema(StrictModel):
    model_id: str
    family: ModelFamily
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    requires_optional_dependency: bool = False


class TrainingConfigSchema(StrictModel):
    random_seed: int = 42
    optional_dependency_policy: OptionalDependencyPolicy = (
        OptionalDependencyPolicy.SKIP_UNAVAILABLE_MODELS
    )
    fallback_split_spec: SplitSpecSchema = Field(default_factory=SplitSpecSchema)
    standardize_linear_models: bool = True
    minimum_train_rows: int = 8


class MLWorkflowSpecSchema(StrictModel):
    feature_spec: FeatureSpecSchema = Field(default_factory=FeatureSpecSchema)
    label_specs: list[LabelSpecSchema] = Field(
        default_factory=lambda: [FutureReturnLabelSpecSchema(horizon_bars=1)],
        min_length=1,
    )
    split_spec: SplitSpecSchema | None = None
    missing_volume_policy: MissingVolumePolicy = MissingVolumePolicy.SKIP_VOLUME_FEATURES
    missing_value_policy: MissingValuePolicy = MissingValuePolicy.DROP_ROW
    task_type: TaskType = TaskType.REGRESSION
    target_label: str | None = None
    model_specs: list[ModelSpecSchema] = Field(default_factory=list)
    training_config: TrainingConfigSchema = Field(default_factory=TrainingConfigSchema)


class RunConfigSchema(StrictModel):
    run_id: str | None = None
    run_name: str | None = None
    random_seed: int = 42
    strict_failures: bool = True
    persist_summary: bool = False
    output_dir: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StrategyRunRequestSchema(StrictModel):
    instrument: InstrumentSchema
    interval: BarInterval
    candle_source: CandleSourceSchema
    strategy_spec: StrategyWorkflowSpecSchema = Field(default_factory=StrategyWorkflowSpecSchema)
    run_config: RunConfigSchema = Field(default_factory=RunConfigSchema)


class MLRunRequestSchema(StrictModel):
    instrument: InstrumentSchema
    interval: BarInterval
    candle_source: CandleSourceSchema
    ml_spec: MLWorkflowSpecSchema = Field(default_factory=MLWorkflowSpecSchema)
    run_config: RunConfigSchema = Field(default_factory=RunConfigSchema)


class HybridRunRequestSchema(StrictModel):
    instrument: InstrumentSchema
    interval: BarInterval
    candle_source: CandleSourceSchema
    strategy_spec: StrategyWorkflowSpecSchema = Field(default_factory=StrategyWorkflowSpecSchema)
    ml_spec: MLWorkflowSpecSchema = Field(default_factory=MLWorkflowSpecSchema)
    run_config: RunConfigSchema = Field(default_factory=RunConfigSchema)


class StepResultSchema(StrictModel):
    step_name: str
    status: str
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandleTimeRangeSchema(StrictModel):
    start: datetime
    end: datetime


class StrategySummarySchema(StrictModel):
    strategy_id: str
    total_trades: int
    total_return_pct: float
    total_net_pnl: float
    max_drawdown_pct: float
    sharpe_ratio: float | None = None


class MLSummarySchema(StrictModel):
    target_label: str
    task_type: TaskType
    best_model_id: str | None = None
    primary_metric_name: str | None = None
    best_validation_value: float | None = None
    best_test_value: float | None = None
    model_count_executed: int
    model_count_skipped: int
    warning_count: int


class RunSummaryResponseSchema(StrictModel):
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    instrument: InstrumentSchema
    interval: BarInterval
    candle_count: int
    candle_source_type: str
    step_results: list[StepResultSchema]
    metadata: dict[str, Any] = Field(default_factory=dict)
    candle_time_range: CandleTimeRangeSchema | None = None
    strategy: StrategySummarySchema | None = None
    ml: MLSummarySchema | None = None


class StrategyTradeRowSchema(StrictModel):
    entry_time: datetime
    exit_time: datetime
    direction: str
    entry_price: float
    exit_price: float
    units: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    bars_held: int
    exit_reason: str


class EquityPointDetailSchema(StrictModel):
    timestamp: datetime
    equity: float
    cash: float
    unrealized_pnl: float
    drawdown_pct: float


class DrawdownPointSchema(StrictModel):
    timestamp: datetime
    drawdown_pct: float


class DrawdownEpisodeSchema(StrictModel):
    peak_time: datetime
    trough_time: datetime
    recovery_time: datetime | None = None
    depth_pct: float
    duration_bars: int
    recovery_bars: int | None = None


class StrategyDetailResponseSchema(StrictModel):
    backtest_summary: dict[str, Any] = Field(default_factory=dict)
    performance: dict[str, Any] = Field(default_factory=dict)
    trade_analysis: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    assumptions: dict[str, str] = Field(default_factory=dict)
    equity_curve: list[EquityPointDetailSchema] = Field(default_factory=list)
    drawdown_curve: list[DrawdownPointSchema] = Field(default_factory=list)
    trades: list[StrategyTradeRowSchema] = Field(default_factory=list)
    drawdown_episodes: list[DrawdownEpisodeSchema] = Field(default_factory=list)


class ModelComparisonEntrySchema(StrictModel):
    model_id: str
    family: str
    primary_metric_name: str
    validation_value: float | None = None
    test_value: float | None = None
    higher_is_better: bool


class FeatureImportanceItemSchema(StrictModel):
    feature: str
    score: float


class ModelReportDetailSchema(StrictModel):
    model_id: str
    family: str
    task_type: str
    skipped: bool
    skip_reason: str | None = None
    metrics_by_split: dict[str, dict[str, Any]] = Field(default_factory=dict)
    feature_importance: list[FeatureImportanceItemSchema] | None = None
    warnings: list[str] = Field(default_factory=list)


class MLDetailResponseSchema(StrictModel):
    target_label: str
    task_type: TaskType
    dataset_metadata: dict[str, Any] = Field(default_factory=dict)
    comparison_table: list[ModelComparisonEntrySchema] = Field(default_factory=list)
    model_reports: list[ModelReportDetailSchema] = Field(default_factory=list)
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class RunDetailResponseSchema(StrictModel):
    summary: RunSummaryResponseSchema
    strategy_detail: StrategyDetailResponseSchema | None = None
    ml_detail: MLDetailResponseSchema | None = None


class StoredRunSummaryListItemSchema(StrictModel):
    run_id: str
    run_name: str | None = None
    workflow_type: str | None = None
    status: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    summary_path: str


class StoredRunSummaryListResponseSchema(StrictModel):
    runs: list[StoredRunSummaryListItemSchema]


class MarketDataPreviewRequestSchema(StrictModel):
    provider_name: str
    instrument: InstrumentSchema
    interval: BarInterval
    start: datetime
    end: datetime
    limit: int | None = Field(default=None, gt=0)


class MarketDataPreviewResponseSchema(StrictModel):
    provider: str
    instrument: InstrumentSchema
    interval: BarInterval
    candles: list[CandleSchema]
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilitiesResponseSchema(StrictModel):
    workflows: list[str]
    strategies: list[str]
    providers: list[str]
    intervals: list[str]
    asset_classes: list[str]
    model_families: list[str]
    feature_flags: dict[str, bool] | None = None
    paper_trading: dict[str, Any] | None = None
    live_execution: dict[str, Any] | None = None
