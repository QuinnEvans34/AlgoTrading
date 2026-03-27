"""Typed contracts for baseline model training and evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

import numpy as np

from ml_data.contracts import MLDatasetArtifact, SplitSpec


class TaskType(str, Enum):
    REGRESSION = "regression"
    CLASSIFICATION = "classification"


class ModelFamily(str, Enum):
    DUMMY_REGRESSOR = "dummy_regressor"
    DUMMY_CLASSIFIER = "dummy_classifier"
    RIDGE_REGRESSOR_NUMPY = "ridge_regressor_np"
    LINEAR_REGRESSION_SKLEARN = "linear_regression_sklearn"
    LOGISTIC_REGRESSION_SKLEARN = "logistic_regression_sklearn"
    RANDOM_FOREST_REGRESSOR_SKLEARN = "random_forest_regressor_sklearn"
    RANDOM_FOREST_CLASSIFIER_SKLEARN = "random_forest_classifier_sklearn"
    GRADIENT_BOOSTING_REGRESSOR_SKLEARN = "gradient_boosting_regressor_sklearn"
    GRADIENT_BOOSTING_CLASSIFIER_SKLEARN = "gradient_boosting_classifier_sklearn"


class OptionalDependencyPolicy(str, Enum):
    SKIP_UNAVAILABLE_MODELS = "skip_unavailable_models"
    ERROR_ON_UNAVAILABLE_MODELS = "error_on_unavailable_models"


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    family: ModelFamily
    hyperparameters: Mapping[str, Any] = field(default_factory=dict)
    requires_optional_dependency: bool = False


@dataclass(frozen=True)
class TrainingConfig:
    random_seed: int = 42
    optional_dependency_policy: OptionalDependencyPolicy = (
        OptionalDependencyPolicy.SKIP_UNAVAILABLE_MODELS
    )
    fallback_split_spec: SplitSpec = field(default_factory=SplitSpec)
    standardize_linear_models: bool = True
    minimum_train_rows: int = 8


@dataclass(frozen=True)
class TrainingRequest:
    dataset: MLDatasetArtifact
    target_label: str
    task_type: TaskType
    model_specs: tuple[ModelSpec, ...] = ()
    config: TrainingConfig = field(default_factory=TrainingConfig)


@dataclass(frozen=True)
class TrainingTable:
    X: np.ndarray
    y: np.ndarray
    feature_names: tuple[str, ...]
    timestamps: tuple[datetime, ...]
    train_indices: tuple[int, ...]
    validation_indices: tuple[int, ...]
    test_indices: tuple[int, ...]


@dataclass(frozen=True)
class SplitPrediction:
    timestamps: tuple[datetime, ...]
    y_true: tuple[float | int, ...]
    y_pred: tuple[float | int, ...]
    y_score: tuple[float, ...] | None = None


@dataclass(frozen=True)
class RegressionMetrics:
    mae: float
    rmse: float
    r2: float | None
    directional_accuracy: float | None
    sample_count: int


@dataclass(frozen=True)
class ClassificationMetrics:
    accuracy: float
    precision: float | None
    recall: float | None
    f1: float | None
    balanced_accuracy: float
    roc_auc: float | None
    confusion_matrix: tuple[tuple[int, ...], ...]
    class_labels: tuple[int, ...]
    positive_class: int | None
    sample_count: int


MetricResult = RegressionMetrics | ClassificationMetrics

