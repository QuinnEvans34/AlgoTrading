"""Baseline model training and evaluation subsystem."""

from .artifacts import ModelComparisonEntry, ModelEvaluationReport, TrainingRunArtifact
from .config import default_model_specs, resolve_model_specs
from .contracts import (
    ClassificationMetrics,
    MetricResult,
    ModelFamily,
    ModelSpec,
    OptionalDependencyPolicy,
    RegressionMetrics,
    SplitPrediction,
    TaskType,
    TrainingConfig,
    TrainingRequest,
    TrainingTable,
)
from .evaluation import (
    classification_metrics,
    evaluate_predictions,
    metric_value,
    primary_metric_higher_is_better,
    primary_metric_name,
    regression_metrics,
)
from .models import (
    OptionalDependencyUnavailableError,
    UnsupportedModelTaskError,
    create_model,
    is_linear_like_family,
    is_optional_family,
    model_supports_task,
)
from .trainer import train_and_evaluate

__all__ = [
    "TaskType",
    "ModelFamily",
    "OptionalDependencyPolicy",
    "ModelSpec",
    "TrainingConfig",
    "TrainingRequest",
    "TrainingTable",
    "SplitPrediction",
    "RegressionMetrics",
    "ClassificationMetrics",
    "MetricResult",
    "ModelEvaluationReport",
    "ModelComparisonEntry",
    "TrainingRunArtifact",
    "default_model_specs",
    "resolve_model_specs",
    "create_model",
    "model_supports_task",
    "is_optional_family",
    "is_linear_like_family",
    "OptionalDependencyUnavailableError",
    "UnsupportedModelTaskError",
    "regression_metrics",
    "classification_metrics",
    "evaluate_predictions",
    "primary_metric_name",
    "primary_metric_higher_is_better",
    "metric_value",
    "train_and_evaluate",
]

