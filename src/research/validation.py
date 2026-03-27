"""Validation helpers for research run requests."""

from __future__ import annotations

from typing import Mapping

from ml_data import DirectionLabelSpec, FutureReturnLabelSpec
from modeling import TaskType

from .contracts import (
    InlineCandleSource,
    MLWorkflowSpec,
    MarketDataFetchSource,
    ResearchRunRequest,
    ResearchWorkflowType,
)

SUPPORTED_STRATEGY_IDS: tuple[str, ...] = ("technical_rule_v1",)


def resolve_ml_target_label(spec: MLWorkflowSpec) -> str:
    if not spec.label_specs:
        raise ValueError("MLWorkflowSpec.label_specs cannot be empty")
    if spec.target_label is not None:
        return spec.target_label
    return spec.label_specs[0].resolved_name()


def _label_type_map(spec: MLWorkflowSpec) -> Mapping[str, str]:
    out: dict[str, str] = {}
    for label_spec in spec.label_specs:
        name = label_spec.resolved_name()
        if isinstance(label_spec, FutureReturnLabelSpec):
            out[name] = "regression"
        elif isinstance(label_spec, DirectionLabelSpec):
            out[name] = "classification"
        else:
            raise ValueError(f"Unsupported label spec type: {type(label_spec)!r}")
    return out


def validate_request(request: ResearchRunRequest) -> None:
    if request.workflow_type in (
        ResearchWorkflowType.STRATEGY_RESEARCH,
        ResearchWorkflowType.HYBRID_RESEARCH,
    ):
        if request.strategy_spec is None:
            raise ValueError("strategy_spec is required for strategy/hybrid workflows")
        if request.strategy_spec.strategy_id not in SUPPORTED_STRATEGY_IDS:
            raise ValueError(
                f"Unsupported strategy_id '{request.strategy_spec.strategy_id}'. "
                f"Supported: {SUPPORTED_STRATEGY_IDS}"
            )

    if request.workflow_type in (
        ResearchWorkflowType.ML_RESEARCH,
        ResearchWorkflowType.HYBRID_RESEARCH,
    ):
        if request.ml_spec is None:
            raise ValueError("ml_spec is required for ml/hybrid workflows")
        target_label = resolve_ml_target_label(request.ml_spec)
        label_type_by_name = _label_type_map(request.ml_spec)
        if target_label not in label_type_by_name:
            raise ValueError(
                f"target_label '{target_label}' not present in ml_spec.label_specs: "
                f"{tuple(label_type_by_name.keys())}"
            )
        target_kind = label_type_by_name[target_label]
        if request.ml_spec.task_type == TaskType.REGRESSION and target_kind != "regression":
            raise ValueError(
                f"TaskType.REGRESSION requires a regression label. "
                f"target_label '{target_label}' is {target_kind}."
            )
        if request.ml_spec.task_type == TaskType.CLASSIFICATION and target_kind != "classification":
            raise ValueError(
                f"TaskType.CLASSIFICATION requires a classification label. "
                f"target_label '{target_label}' is {target_kind}."
            )

    candle_source = request.candle_source
    if isinstance(candle_source, InlineCandleSource):
        if len(candle_source.candles) == 0:
            raise ValueError("Inline candle source must provide at least one candle")
    elif isinstance(candle_source, MarketDataFetchSource):
        if candle_source.start >= candle_source.end:
            raise ValueError("MarketDataFetchSource.start must be before end")
        if candle_source.limit is not None and candle_source.limit <= 0:
            raise ValueError("MarketDataFetchSource.limit must be > 0 when provided")
        if candle_source.provider_name.strip() == "":
            raise ValueError("MarketDataFetchSource.provider_name cannot be empty")
    else:
        raise ValueError(f"Unsupported candle source: {type(candle_source)!r}")

