"""Orchestration for deterministic ML dataset artifact generation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from market_data.contracts import ensure_utc

from .contracts import (
    DatasetMetadata,
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    LabelSpec,
    MLDatasetArtifact,
    MLDatasetRequest,
    MLDatasetRow,
)
from .features import compute_feature_values
from .labels import compute_label_values
from .splits import build_chronological_splits
from .validation import sorted_unique_candles, validate_request


def _feature_spec_snapshot(spec: FeatureSpec) -> dict[str, Any]:
    return {
        "return_windows": list(spec.return_windows),
        "log_return_windows": list(spec.log_return_windows),
        "volatility_windows": list(spec.volatility_windows),
        "momentum_windows": list(spec.momentum_windows),
        "sma_windows": list(spec.sma_windows),
        "sma_crossover_pairs": [list(pair) for pair in spec.sma_crossover_pairs],
        "atr_windows": list(spec.atr_windows),
        "zscore_windows": list(spec.zscore_windows),
        "include_candle_structure": spec.include_candle_structure,
        "include_volume_features": spec.include_volume_features,
        "volume_zscore_windows": list(spec.volume_zscore_windows),
    }


def _label_spec_snapshot(label_specs: tuple[LabelSpec, ...]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for spec in label_specs:
        if isinstance(spec, FutureReturnLabelSpec):
            out.append(
                {
                    "type": "future_return",
                    "name": spec.resolved_name(),
                    "horizon_bars": spec.horizon_bars,
                    "price_field": spec.price_field,
                }
            )
            continue
        if isinstance(spec, DirectionLabelSpec):
            out.append(
                {
                    "type": "direction",
                    "name": spec.resolved_name(),
                    "horizon_bars": spec.horizon_bars,
                    "threshold": spec.threshold,
                    "price_field": spec.price_field,
                }
            )
            continue
        raise ValueError(f"Unsupported label spec type: {type(spec)!r}")
    return out


def _build_signature(
    *,
    request: MLDatasetRequest,
    feature_names: tuple[str, ...],
    label_names: tuple[str, ...],
    candle_timestamps: tuple[str, ...],
) -> str:
    payload = {
        "instrument_symbol": request.instrument.symbol,
        "asset_class": request.instrument.asset_class.value,
        "interval": request.interval.value,
        "feature_spec": _feature_spec_snapshot(request.feature_spec),
        "label_specs": _label_spec_snapshot(request.label_specs),
        "feature_names": list(feature_names),
        "label_names": list(label_names),
        "missing_volume_policy": request.missing_volume_policy.value,
        "missing_value_policy": request.missing_value_policy.value,
        "split_spec": (
            None
            if request.split_spec is None
            else {
                "train_fraction": request.split_spec.train_fraction,
                "validation_fraction": request.split_spec.validation_fraction,
                "test_fraction": request.split_spec.test_fraction,
                "gap_bars": request.split_spec.gap_bars,
            }
        ),
        "candle_timestamps": list(candle_timestamps),
    }
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def build_ml_dataset(request: MLDatasetRequest) -> MLDatasetArtifact:
    """Build a deterministic, leakage-safe ML dataset artifact."""
    validate_request(request)
    candles = sorted_unique_candles(request.candles)

    feature_result = compute_feature_values(
        candles,
        spec=request.feature_spec,
        missing_volume_policy=request.missing_volume_policy,
    )
    label_result = compute_label_values(candles, label_specs=request.label_specs)

    feature_names = tuple(feature_result.feature_values.keys())
    label_names = tuple(label_result.label_values.keys())

    if len(feature_names) == 0:
        raise ValueError("No features were produced; check FeatureSpec configuration")

    max_lookback = feature_result.max_lookback_bars
    max_horizon = label_result.max_horizon_bars
    start_index = max_lookback
    end_exclusive = len(candles) - max_horizon
    if end_exclusive <= start_index:
        raise ValueError(
            "Not enough candles after lookback/horizon alignment to build dataset rows"
        )

    rows: list[MLDatasetRow] = []
    dropped_missing_rows = 0

    for idx in range(start_index, end_exclusive):
        feature_map: dict[str, float] = {}
        label_map: dict[str, float | int] = {}

        row_has_missing = False
        for name in feature_names:
            value = feature_result.feature_values[name][idx]
            if value is None:
                row_has_missing = True
                break
            feature_map[name] = float(value)
        if row_has_missing:
            dropped_missing_rows += 1
            continue

        for name in label_names:
            value = label_result.label_values[name][idx]
            if value is None:
                row_has_missing = True
                break
            if isinstance(value, int):
                label_map[name] = value
            else:
                label_map[name] = float(value)
        if row_has_missing:
            dropped_missing_rows += 1
            continue

        rows.append(
            MLDatasetRow(
                timestamp=ensure_utc(candles[idx].timestamp),
                features=feature_map,
                labels=label_map,
            )
        )

    if len(rows) == 0:
        raise ValueError(
            "All candidate rows were dropped due to missing values; adjust windows/specs"
        )

    timestamp_snapshot = tuple(ensure_utc(c.timestamp).isoformat() for c in candles)
    signature = _build_signature(
        request=request,
        feature_names=feature_names,
        label_names=label_names,
        candle_timestamps=timestamp_snapshot,
    )
    dataset_id = request.dataset_id or f"mlset-{signature[:12]}"

    request_snapshot = {
        "dataset_id": dataset_id,
        "feature_spec": _feature_spec_snapshot(request.feature_spec),
        "label_specs": _label_spec_snapshot(request.label_specs),
        "missing_volume_policy": request.missing_volume_policy.value,
        "missing_value_policy": request.missing_value_policy.value,
        "split_spec": (
            None
            if request.split_spec is None
            else {
                "train_fraction": request.split_spec.train_fraction,
                "validation_fraction": request.split_spec.validation_fraction,
                "test_fraction": request.split_spec.test_fraction,
                "gap_bars": request.split_spec.gap_bars,
            }
        ),
        "skipped_features": list(feature_result.skipped_features),
    }

    metadata = DatasetMetadata(
        dataset_id=dataset_id,
        instrument_symbol=request.instrument.symbol,
        interval=request.interval,
        feature_names=feature_names,
        label_names=label_names,
        max_feature_lookback_bars=max_lookback,
        max_label_horizon_bars=max_horizon,
        input_row_count=len(candles),
        output_row_count=len(rows),
        dropped_warmup_rows=start_index,
        dropped_horizon_rows=max_horizon,
        dropped_missing_rows=dropped_missing_rows,
        start_timestamp=rows[0].timestamp if rows else None,
        end_timestamp=rows[-1].timestamp if rows else None,
        signature_sha256=signature,
        assumptions={
            "chronological_processing": "Rows are generated in strict timestamp order.",
            "leakage_policy": "Features use only candles up to row timestamp; labels may use forward horizon by spec.",
            "missing_value_policy": request.missing_value_policy.value,
        },
        request_snapshot=request_snapshot,
    )

    splits = None
    row_tuple = tuple(rows)
    if request.split_spec is not None:
        splits = build_chronological_splits(row_tuple, split_spec=request.split_spec)

    return MLDatasetArtifact(
        instrument=request.instrument,
        interval=request.interval,
        rows=row_tuple,
        feature_names=feature_names,
        label_names=label_names,
        metadata=metadata,
        splits=splits,
    )

