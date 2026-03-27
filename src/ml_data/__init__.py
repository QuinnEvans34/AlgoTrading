"""ML dataset and feature engineering subsystem."""

from .contracts import (
    DatasetMetadata,
    DatasetSplits,
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    LabelSpec,
    MLDatasetArtifact,
    MLDatasetRequest,
    MLDatasetRow,
    MissingValuePolicy,
    MissingVolumePolicy,
    SplitPartition,
    SplitSpec,
    label_names,
)
from .dataset_builder import build_ml_dataset
from .features import FeatureComputationResult, compute_feature_values
from .labels import LabelComputationResult, compute_label_values
from .splits import build_chronological_splits
from .validation import sorted_unique_candles, validate_request, validate_split_spec

__all__ = [
    "MissingVolumePolicy",
    "MissingValuePolicy",
    "FeatureSpec",
    "FutureReturnLabelSpec",
    "DirectionLabelSpec",
    "LabelSpec",
    "SplitSpec",
    "MLDatasetRequest",
    "MLDatasetRow",
    "SplitPartition",
    "DatasetSplits",
    "DatasetMetadata",
    "MLDatasetArtifact",
    "label_names",
    "FeatureComputationResult",
    "LabelComputationResult",
    "compute_feature_values",
    "compute_label_values",
    "build_chronological_splits",
    "sorted_unique_candles",
    "validate_split_spec",
    "validate_request",
    "build_ml_dataset",
]

