"""Validation helpers for ML dataset request configuration and inputs."""

from __future__ import annotations

from typing import Sequence

from market_data.contracts import Candle, ensure_utc

from .contracts import LabelSpec, MLDatasetRequest, SplitSpec


def sorted_unique_candles(candles: Sequence[Candle]) -> tuple[Candle, ...]:
    ordered = tuple(sorted(candles, key=lambda candle: ensure_utc(candle.timestamp)))
    if not ordered:
        raise ValueError("ML dataset builder requires at least one candle")
    for i in range(1, len(ordered)):
        prev = ensure_utc(ordered[i - 1].timestamp)
        curr = ensure_utc(ordered[i].timestamp)
        if curr <= prev:
            raise ValueError("Candle timestamps must be strictly increasing and unique")
    return ordered


def validate_label_specs(label_specs: Sequence[LabelSpec]) -> tuple[str, ...]:
    if not label_specs:
        raise ValueError("At least one label spec is required")
    names = [spec.resolved_name() for spec in label_specs]
    if len(set(names)) != len(names):
        raise ValueError("Label names must be unique")
    for spec in label_specs:
        if spec.horizon_bars <= 0:
            raise ValueError("Label horizon_bars must be > 0")
        if spec.price_field != "close":
            raise ValueError("Only price_field='close' is supported in this phase")
    return tuple(names)


def validate_split_spec(split_spec: SplitSpec) -> None:
    if split_spec.train_fraction < 0 or split_spec.validation_fraction < 0 or split_spec.test_fraction < 0:
        raise ValueError("Split fractions must be non-negative")
    total = split_spec.train_fraction + split_spec.validation_fraction + split_spec.test_fraction
    if abs(total - 1.0) > 1e-9:
        raise ValueError("Split fractions must sum to 1.0")
    if split_spec.gap_bars < 0:
        raise ValueError("gap_bars must be >= 0")


def validate_request(request: MLDatasetRequest) -> None:
    if request.missing_value_policy.value != "drop_row":
        raise ValueError(f"Unsupported missing value policy: {request.missing_value_policy}")
    validate_label_specs(request.label_specs)
    if request.split_spec is not None:
        validate_split_spec(request.split_spec)

