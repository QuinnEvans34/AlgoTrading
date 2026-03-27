"""Structured artifacts for model training and evaluation outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .contracts import MetricResult, ModelFamily, SplitPrediction, TaskType


@dataclass(frozen=True)
class ModelEvaluationReport:
    model_id: str
    family: ModelFamily
    task_type: TaskType
    skipped: bool
    skip_reason: str | None
    metrics_by_split: Mapping[str, MetricResult] = field(default_factory=dict)
    predictions_by_split: Mapping[str, SplitPrediction] = field(default_factory=dict)
    feature_importance: tuple[tuple[str, float], ...] | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelComparisonEntry:
    model_id: str
    family: ModelFamily
    primary_metric_name: str
    validation_value: float | None
    test_value: float | None
    higher_is_better: bool


@dataclass(frozen=True)
class TrainingRunArtifact:
    target_label: str
    task_type: TaskType
    model_reports: tuple[ModelEvaluationReport, ...]
    comparison_table: tuple[ModelComparisonEntry, ...]
    run_metadata: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

