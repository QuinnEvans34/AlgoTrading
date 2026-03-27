"""Task-specific evaluation metrics for baseline modeling."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from .contracts import (
    ClassificationMetrics,
    MetricResult,
    RegressionMetrics,
    TaskType,
)


def _safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if ss_tot == 0:
        return None
    return 1.0 - (ss_res / ss_tot)


def regression_metrics(y_true: Sequence[float], y_pred: Sequence[float]) -> RegressionMetrics:
    true = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    mae = float(np.mean(np.abs(true - pred)))
    directional_accuracy = float(np.mean((true > 0) == (pred > 0))) if len(true) else None
    return RegressionMetrics(
        mae=mae,
        rmse=_rmse(true, pred),
        r2=_r2(true, pred),
        directional_accuracy=directional_accuracy,
        sample_count=int(len(true)),
    )


def _binary_confusion(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[int, int, int, int]:
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    return tn, fp, fn, tp


def _confusion_matrix_multiclass(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_labels: Sequence[int],
) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for actual in class_labels:
        row: list[int] = []
        for predicted in class_labels:
            row.append(int(np.sum((y_true == actual) & (y_pred == predicted))))
        rows.append(tuple(row))
    return tuple(rows)


def _balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray, classes: np.ndarray) -> float:
    recalls: list[float] = []
    for cls in classes:
        positives = np.sum(y_true == cls)
        if positives == 0:
            continue
        recalls.append(float(np.sum((y_true == cls) & (y_pred == cls)) / positives))
    return float(np.mean(recalls)) if recalls else 0.0


def _rank_with_ties(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values)
    sorted_values = values[order]
    ranks_sorted = np.zeros(len(values), dtype=float)

    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and sorted_values[j] == sorted_values[i]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        ranks_sorted[i:j] = avg_rank
        i = j

    ranks = np.empty(len(values), dtype=float)
    ranks[order] = ranks_sorted
    return ranks


def _roc_auc_binary(y_true: np.ndarray, y_score: np.ndarray) -> float | None:
    pos = y_true == 1
    neg = y_true == 0
    n_pos = int(np.sum(pos))
    n_neg = int(np.sum(neg))
    if n_pos == 0 or n_neg == 0:
        return None

    ranks = _rank_with_ties(y_score)
    sum_pos_ranks = float(np.sum(ranks[pos]))
    auc = (sum_pos_ranks - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg)
    return float(auc)


def classification_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    y_score: Sequence[float] | None = None,
) -> ClassificationMetrics:
    true = np.asarray(y_true, dtype=int)
    pred = np.asarray(y_pred, dtype=int)
    classes = np.unique(np.concatenate([true, pred]))
    class_labels = tuple(int(x) for x in classes.tolist())
    cm = _confusion_matrix_multiclass(true, pred, classes)
    accuracy = float(np.mean(true == pred))
    balanced_accuracy = _balanced_accuracy(true, pred, classes)

    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    positive_class: int | None = None

    if set(class_labels) <= {0, 1} and len(class_labels) >= 1:
        positive_class = 1 if 1 in class_labels else class_labels[-1]
        tn, fp, fn, tp = _binary_confusion(true, pred)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        if precision is not None and recall is not None and (precision + recall) > 0:
            f1 = (2.0 * precision * recall) / (precision + recall)
        if y_score is not None:
            scores = np.asarray(y_score, dtype=float)
            if len(scores) == len(true):
                roc_auc = _roc_auc_binary(true, scores)

    return ClassificationMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        balanced_accuracy=balanced_accuracy,
        roc_auc=roc_auc,
        confusion_matrix=cm,
        class_labels=class_labels,
        positive_class=positive_class,
        sample_count=int(len(true)),
    )


def evaluate_predictions(
    *,
    task_type: TaskType,
    y_true: Sequence[float | int],
    y_pred: Sequence[float | int],
    y_score: Sequence[float] | None = None,
) -> MetricResult:
    if task_type == TaskType.REGRESSION:
        return regression_metrics(
            y_true=[float(v) for v in y_true],
            y_pred=[float(v) for v in y_pred],
        )
    if task_type == TaskType.CLASSIFICATION:
        return classification_metrics(
            y_true=[int(v) for v in y_true],
            y_pred=[int(v) for v in y_pred],
            y_score=None if y_score is None else [float(v) for v in y_score],
        )
    raise ValueError(f"Unsupported task type: {task_type}")


def primary_metric_name(task_type: TaskType) -> str:
    return "rmse" if task_type == TaskType.REGRESSION else "f1"


def primary_metric_higher_is_better(task_type: TaskType) -> bool:
    return task_type == TaskType.CLASSIFICATION


def metric_value(metric: MetricResult, name: str) -> float | None:
    value = getattr(metric, name, None)
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return float(value)

