"""Research run API orchestration and schema-to-domain mapping."""

from __future__ import annotations

from typing import Any

from config import AppSettings
from market_data import Candle
from ml_data import (
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    MissingValuePolicy,
    MissingVolumePolicy,
    SplitSpec,
)
from modeling import ModelSpec, OptionalDependencyPolicy, TaskType, TrainingConfig
from research import (
    InlineCandleSource,
    MLWorkflowSpec,
    MarketDataFetchSource,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    StrategyWorkflowSpec,
)

from ..config import APISettings
from ..schemas import (
    CandleSchema,
    DirectionLabelSpecSchema,
    FutureReturnLabelSpecSchema,
    HybridRunRequestSchema,
    InlineCandleSourceSchema,
    MarketDataFetchSourceSchema,
    MLRunRequestSchema,
    ModelSpecSchema,
    RunConfigSchema,
    RunSummaryResponseSchema,
    SplitSpecSchema,
    StrategyRunRequestSchema,
)
from ..serializers import serialize_run_summary
from .common import ensure_feature_enabled, to_instrument


class ResearchAPIService:
    def __init__(
        self,
        *,
        settings: APISettings,
        app_settings: AppSettings,
        research_runner: ResearchRunner,
    ) -> None:
        self._settings = settings
        self._app_settings = app_settings
        self._research_runner = research_runner

    def run_strategy(
        self,
        request: StrategyRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "research_api_enabled",
            code="research_disabled",
            message="Research run endpoints are disabled by feature flag.",
        )
        run_request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
            instrument=to_instrument(request.instrument),
            interval=request.interval,
            candle_source=self._to_candle_source(request.candle_source),
            strategy_spec=self._to_strategy_spec(request.strategy_spec),
            run_config=self._to_run_config(request.run_config),
        )
        artifact = self._research_runner.run(run_request)
        return serialize_run_summary(artifact)

    def run_ml(
        self,
        request: MLRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "research_api_enabled",
            code="research_disabled",
            message="Research run endpoints are disabled by feature flag.",
        )
        run_request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.ML_RESEARCH,
            instrument=to_instrument(request.instrument),
            interval=request.interval,
            candle_source=self._to_candle_source(request.candle_source),
            ml_spec=self._to_ml_spec(request.ml_spec),
            run_config=self._to_run_config(request.run_config),
        )
        artifact = self._research_runner.run(run_request)
        return serialize_run_summary(artifact)

    def run_hybrid(
        self,
        request: HybridRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "research_api_enabled",
            code="research_disabled",
            message="Research run endpoints are disabled by feature flag.",
        )
        run_request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.HYBRID_RESEARCH,
            instrument=to_instrument(request.instrument),
            interval=request.interval,
            candle_source=self._to_candle_source(request.candle_source),
            strategy_spec=self._to_strategy_spec(request.strategy_spec),
            ml_spec=self._to_ml_spec(request.ml_spec),
            run_config=self._to_run_config(request.run_config),
        )
        artifact = self._research_runner.run(run_request)
        return serialize_run_summary(artifact)

    @staticmethod
    def _to_candle(candle: CandleSchema) -> Candle:
        return Candle(
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        )

    def _to_candle_source(
        self,
        candle_source: InlineCandleSourceSchema | MarketDataFetchSourceSchema,
    ) -> InlineCandleSource | MarketDataFetchSource:
        if isinstance(candle_source, InlineCandleSourceSchema):
            return InlineCandleSource(
                candles=tuple(self._to_candle(candle) for candle in candle_source.candles)
            )
        return MarketDataFetchSource(
            provider_name=candle_source.provider_name,
            start=candle_source.start,
            end=candle_source.end,
            limit=candle_source.limit,
        )

    def _to_run_config(self, config: RunConfigSchema) -> ResearchRunConfig:
        persist_summary = config.persist_summary
        output_dir = config.output_dir
        if output_dir is None and persist_summary:
            output_dir = self._settings.default_run_output_dir
        return ResearchRunConfig(
            run_id=config.run_id,
            run_name=config.run_name,
            random_seed=config.random_seed,
            strict_failures=config.strict_failures,
            persist_summary=persist_summary,
            output_dir=output_dir,
            metadata=dict(config.metadata),
        )

    @staticmethod
    def _to_strategy_spec(schema: Any) -> StrategyWorkflowSpec:
        return StrategyWorkflowSpec(
            strategy_id=schema.strategy_id,
            backtest_config=schema.backtest_config.to_domain(),
            diagnostics_config=(
                None if schema.diagnostics_config is None else schema.diagnostics_config.to_domain()
            ),
        )

    @staticmethod
    def _to_feature_spec(schema: Any) -> FeatureSpec:
        return FeatureSpec(
            return_windows=schema.return_windows,
            log_return_windows=schema.log_return_windows,
            volatility_windows=schema.volatility_windows,
            momentum_windows=schema.momentum_windows,
            sma_windows=schema.sma_windows,
            sma_crossover_pairs=schema.sma_crossover_pairs,
            atr_windows=schema.atr_windows,
            zscore_windows=schema.zscore_windows,
            include_candle_structure=schema.include_candle_structure,
            include_volume_features=schema.include_volume_features,
            volume_zscore_windows=schema.volume_zscore_windows,
        )

    @staticmethod
    def _to_split_spec(schema: SplitSpecSchema | None) -> SplitSpec | None:
        if schema is None:
            return None
        return SplitSpec(
            train_fraction=schema.train_fraction,
            validation_fraction=schema.validation_fraction,
            test_fraction=schema.test_fraction,
            gap_bars=schema.gap_bars,
        )

    @staticmethod
    def _to_label_specs(label_specs: list[Any]) -> tuple[Any, ...]:
        out: list[Any] = []
        for label_spec in label_specs:
            if isinstance(label_spec, FutureReturnLabelSpecSchema):
                out.append(
                    FutureReturnLabelSpec(
                        horizon_bars=label_spec.horizon_bars,
                        name=label_spec.name,
                        price_field=label_spec.price_field,
                    )
                )
                continue
            if isinstance(label_spec, DirectionLabelSpecSchema):
                out.append(
                    DirectionLabelSpec(
                        horizon_bars=label_spec.horizon_bars,
                        threshold=label_spec.threshold,
                        name=label_spec.name,
                        price_field=label_spec.price_field,
                    )
                )
                continue
            raise ValueError(f"Unsupported label spec schema: {type(label_spec)!r}")
        return tuple(out)

    @staticmethod
    def _to_model_specs(model_specs: list[ModelSpecSchema]) -> tuple[ModelSpec, ...]:
        return tuple(
            ModelSpec(
                model_id=spec.model_id,
                family=spec.family,
                hyperparameters=spec.hyperparameters,
                requires_optional_dependency=spec.requires_optional_dependency,
            )
            for spec in model_specs
        )

    @staticmethod
    def _to_training_config(schema: Any) -> TrainingConfig:
        return TrainingConfig(
            random_seed=schema.random_seed,
            optional_dependency_policy=OptionalDependencyPolicy(schema.optional_dependency_policy),
            fallback_split_spec=SplitSpec(
                train_fraction=schema.fallback_split_spec.train_fraction,
                validation_fraction=schema.fallback_split_spec.validation_fraction,
                test_fraction=schema.fallback_split_spec.test_fraction,
                gap_bars=schema.fallback_split_spec.gap_bars,
            ),
            standardize_linear_models=schema.standardize_linear_models,
            minimum_train_rows=schema.minimum_train_rows,
        )

    def _to_ml_spec(self, schema: Any) -> MLWorkflowSpec:
        return MLWorkflowSpec(
            feature_spec=self._to_feature_spec(schema.feature_spec),
            label_specs=self._to_label_specs(schema.label_specs),
            split_spec=self._to_split_spec(schema.split_spec),
            missing_volume_policy=MissingVolumePolicy(schema.missing_volume_policy),
            missing_value_policy=MissingValuePolicy(schema.missing_value_policy),
            task_type=TaskType(schema.task_type),
            target_label=schema.target_label,
            model_specs=self._to_model_specs(schema.model_specs),
            training_config=self._to_training_config(schema.training_config),
        )
