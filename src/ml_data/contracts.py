"""Typed contracts for ML dataset and feature engineering workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

from market_data.contracts import BarInterval, Candle, Instrument


class MissingVolumePolicy(str, Enum):
    SKIP_VOLUME_FEATURES = "skip_volume_features"
    REQUIRE_VOLUME = "require_volume"


class MissingValuePolicy(str, Enum):
    DROP_ROW = "drop_row"


@dataclass(frozen=True)
class FeatureSpec:
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


@dataclass(frozen=True)
class FutureReturnLabelSpec:
    horizon_bars: int
    name: str | None = None
    price_field: str = "close"

    def resolved_name(self) -> str:
        return self.name or f"future_return_h{self.horizon_bars}"


@dataclass(frozen=True)
class DirectionLabelSpec:
    horizon_bars: int
    threshold: float = 0.0
    name: str | None = None
    price_field: str = "close"

    def resolved_name(self) -> str:
        if self.name is not None:
            return self.name
        threshold_repr = str(self.threshold).replace("-", "m").replace(".", "p")
        return f"direction_up_h{self.horizon_bars}_thr_{threshold_repr}"


LabelSpec = FutureReturnLabelSpec | DirectionLabelSpec


@dataclass(frozen=True)
class SplitSpec:
    train_fraction: float = 0.70
    validation_fraction: float = 0.15
    test_fraction: float = 0.15
    gap_bars: int = 0


@dataclass(frozen=True)
class MLDatasetRequest:
    instrument: Instrument
    interval: BarInterval
    candles: tuple[Candle, ...]
    feature_spec: FeatureSpec = FeatureSpec()
    label_specs: tuple[LabelSpec, ...] = (FutureReturnLabelSpec(horizon_bars=1),)
    split_spec: SplitSpec | None = None
    dataset_id: str | None = None
    missing_volume_policy: MissingVolumePolicy = MissingVolumePolicy.SKIP_VOLUME_FEATURES
    missing_value_policy: MissingValuePolicy = MissingValuePolicy.DROP_ROW


@dataclass(frozen=True)
class MLDatasetRow:
    timestamp: datetime
    features: Mapping[str, float]
    labels: Mapping[str, float | int]


@dataclass(frozen=True)
class SplitPartition:
    name: str
    indices: tuple[int, ...]
    rows: tuple[MLDatasetRow, ...]


@dataclass(frozen=True)
class DatasetSplits:
    train: SplitPartition
    validation: SplitPartition
    test: SplitPartition
    dropped_gap_indices: tuple[int, ...] = ()


@dataclass(frozen=True)
class DatasetMetadata:
    dataset_id: str
    instrument_symbol: str
    interval: BarInterval
    feature_names: tuple[str, ...]
    label_names: tuple[str, ...]
    max_feature_lookback_bars: int
    max_label_horizon_bars: int
    input_row_count: int
    output_row_count: int
    dropped_warmup_rows: int
    dropped_horizon_rows: int
    dropped_missing_rows: int
    start_timestamp: datetime | None
    end_timestamp: datetime | None
    signature_sha256: str
    assumptions: Mapping[str, str] = field(default_factory=dict)
    request_snapshot: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MLDatasetArtifact:
    instrument: Instrument
    interval: BarInterval
    rows: tuple[MLDatasetRow, ...]
    feature_names: tuple[str, ...]
    label_names: tuple[str, ...]
    metadata: DatasetMetadata
    splits: DatasetSplits | None = None

    def to_records(self) -> list[dict[str, float | int | str]]:
        """Convert rows to flat record dicts for downstream scripts/notebooks."""
        records: list[dict[str, float | int | str]] = []
        for row in self.rows:
            record: dict[str, float | int | str] = {"timestamp": row.timestamp.isoformat()}
            for name in self.feature_names:
                record[f"feature:{name}"] = row.features[name]
            for name in self.label_names:
                record[f"label:{name}"] = row.labels[name]
            records.append(record)
        return records


def label_names(label_specs: Sequence[LabelSpec]) -> tuple[str, ...]:
    return tuple(spec.resolved_name() for spec in label_specs)

