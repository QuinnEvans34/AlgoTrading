"""End-to-end model training and evaluation orchestration."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

from ml_data.splits import build_chronological_splits

from .artifacts import ModelComparisonEntry, ModelEvaluationReport, TrainingRunArtifact
from .config import resolve_model_specs
from .contracts import (
    MetricResult,
    OptionalDependencyPolicy,
    SplitPrediction,
    TaskType,
    TrainingRequest,
    TrainingTable,
)
from .evaluation import (
    evaluate_predictions,
    metric_value,
    primary_metric_higher_is_better,
    primary_metric_name,
)
from .models import (
    OptionalDependencyUnavailableError,
    UnsupportedModelTaskError,
    create_model,
)


def _table_from_request(request: TrainingRequest) -> TrainingTable:
    dataset = request.dataset
    if request.target_label not in dataset.label_names:
        raise ValueError(
            f"target_label '{request.target_label}' not present in dataset labels: {dataset.label_names}"
        )
    if len(dataset.rows) == 0:
        raise ValueError("Dataset contains zero rows")

    X_rows: list[list[float]] = []
    y_rows: list[float | int] = []
    timestamps = []
    for row in dataset.rows:
        feature_vector = [float(row.features[name]) for name in dataset.feature_names]
        X_rows.append(feature_vector)
        y_rows.append(row.labels[request.target_label])
        timestamps.append(row.timestamp)

    X = np.asarray(X_rows, dtype=float)
    y = np.asarray(y_rows)
    if request.task_type == TaskType.REGRESSION:
        y = y.astype(float)
    else:
        if not np.all(np.isfinite(y.astype(float))):
            raise ValueError("Classification target contains non-finite values")
        rounded = np.rint(y.astype(float))
        if not np.allclose(rounded, y.astype(float)):
            raise ValueError("Classification target must contain integer class labels")
        y = rounded.astype(int)

    if not np.all(np.isfinite(X)):
        raise ValueError("Feature matrix contains NaN or infinite values")
    if not np.all(np.isfinite(y.astype(float))):
        raise ValueError("Target vector contains NaN or infinite values")

    if dataset.splits is not None:
        train_indices = dataset.splits.train.indices
        validation_indices = dataset.splits.validation.indices
        test_indices = dataset.splits.test.indices
    else:
        split = build_chronological_splits(
            dataset.rows,
            split_spec=request.config.fallback_split_spec,
        )
        train_indices = split.train.indices
        validation_indices = split.validation.indices
        test_indices = split.test.indices

    if len(train_indices) < request.config.minimum_train_rows:
        raise ValueError(
            f"Not enough train rows ({len(train_indices)}) for minimum_train_rows={request.config.minimum_train_rows}"
        )
    return TrainingTable(
        X=X,
        y=y,
        feature_names=dataset.feature_names,
        timestamps=tuple(timestamps),
        train_indices=train_indices,
        validation_indices=validation_indices,
        test_indices=test_indices,
    )


def _drop_zero_variance_features(
    table: TrainingTable,
) -> tuple[TrainingTable, tuple[str, ...], tuple[str, ...]]:
    train_X = table.X[list(table.train_indices), :]
    variances = np.var(train_X, axis=0)
    keep_mask = variances > 0.0
    kept_names = tuple(
        name for name, keep in zip(table.feature_names, keep_mask, strict=True) if keep
    )
    dropped_names = tuple(
        name for name, keep in zip(table.feature_names, keep_mask, strict=True) if not keep
    )
    if len(kept_names) == 0:
        raise ValueError("All features have zero variance in train split")
    reduced = TrainingTable(
        X=table.X[:, keep_mask],
        y=table.y,
        feature_names=kept_names,
        timestamps=table.timestamps,
        train_indices=table.train_indices,
        validation_indices=table.validation_indices,
        test_indices=table.test_indices,
    )
    return reduced, kept_names, dropped_names


def _standardize_using_train(
    table: TrainingTable,
) -> tuple[np.ndarray, np.ndarray]:
    train_X = table.X[list(table.train_indices), :]
    mean = np.mean(train_X, axis=0)
    std = np.std(train_X, axis=0)
    std = np.where(std == 0.0, 1.0, std)
    return mean, std


def _slice(table: TrainingTable, indices: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    if len(indices) == 0:
        return np.empty((0, table.X.shape[1]), dtype=float), np.empty((0,), dtype=table.y.dtype)
    idx = list(indices)
    return table.X[idx, :], table.y[idx]


def _split_prediction(
    *,
    table: TrainingTable,
    indices: tuple[int, ...],
    y_pred: np.ndarray,
    y_score: np.ndarray | None,
) -> SplitPrediction:
    idx = list(indices)
    y_true_slice = table.y[idx]
    timestamps = tuple(table.timestamps[i] for i in indices)
    y_true: tuple[float | int, ...]
    y_pred_out: tuple[float | int, ...]
    if np.issubdtype(y_true_slice.dtype, np.integer):
        y_true = tuple(int(v) for v in y_true_slice.tolist())
        y_pred_out = tuple(int(v) for v in y_pred.tolist())
    else:
        y_true = tuple(float(v) for v in y_true_slice.tolist())
        y_pred_out = tuple(float(v) for v in y_pred.tolist())
    scores = None if y_score is None else tuple(float(v) for v in y_score.tolist())
    return SplitPrediction(
        timestamps=timestamps,
        y_true=y_true,
        y_pred=y_pred_out,
        y_score=scores,
    )


def _fit_and_report_model(
    *,
    request: TrainingRequest,
    table: TrainingTable,
    model_spec,
) -> ModelEvaluationReport:  # noqa: ANN001
    try:
        model = create_model(
            model_spec,
            task_type=request.task_type,
            random_seed=request.config.random_seed,
        )
    except OptionalDependencyUnavailableError as exc:
        if request.config.optional_dependency_policy == OptionalDependencyPolicy.ERROR_ON_UNAVAILABLE_MODELS:
            raise
        return ModelEvaluationReport(
            model_id=model_spec.model_id,
            family=model_spec.family,
            task_type=request.task_type,
            skipped=True,
            skip_reason=str(exc),
            warnings=(str(exc),),
        )
    except UnsupportedModelTaskError:
        raise

    # Optional scaling for linear-like models.
    X_train, y_train = _slice(table, table.train_indices)
    if model.uses_scaling and request.config.standardize_linear_models:
        mean, std = _standardize_using_train(table)
        X_all = (table.X - mean) / std
    else:
        X_all = table.X

    def split_arrays(indices: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
        if len(indices) == 0:
            return np.empty((0, X_all.shape[1]), dtype=float), np.empty((0,), dtype=table.y.dtype)
        idx = list(indices)
        return X_all[idx, :], table.y[idx]

    X_train_model, y_train_model = split_arrays(table.train_indices)
    model.fit(X_train_model, y_train_model)

    metrics_by_split: dict[str, MetricResult] = {}
    predictions_by_split: dict[str, SplitPrediction] = {}
    for split_name, indices in (
        ("train", table.train_indices),
        ("validation", table.validation_indices),
        ("test", table.test_indices),
    ):
        X_split, y_split = split_arrays(indices)
        if len(indices) == 0:
            continue
        y_pred = np.asarray(model.predict(X_split))
        if request.task_type == TaskType.CLASSIFICATION:
            y_pred = y_pred.astype(int)
        else:
            y_pred = y_pred.astype(float)

        score = model.predict_scores(X_split)
        metrics = evaluate_predictions(
            task_type=request.task_type,
            y_true=y_split.tolist(),
            y_pred=y_pred.tolist(),
            y_score=None if score is None else score.tolist(),
        )
        metrics_by_split[split_name] = metrics
        predictions_by_split[split_name] = _split_prediction(
            table=table,
            indices=indices,
            y_pred=y_pred,
            y_score=score,
        )

    feature_importance = model.feature_importance(table.feature_names)
    return ModelEvaluationReport(
        model_id=model_spec.model_id,
        family=model_spec.family,
        task_type=request.task_type,
        skipped=False,
        skip_reason=None,
        metrics_by_split=metrics_by_split,
        predictions_by_split=predictions_by_split,
        feature_importance=feature_importance,
    )


def _comparison_table(
    *,
    task_type: TaskType,
    reports: tuple[ModelEvaluationReport, ...],
) -> tuple[ModelComparisonEntry, ...]:
    primary_name = primary_metric_name(task_type)
    higher_is_better = primary_metric_higher_is_better(task_type)
    entries: list[ModelComparisonEntry] = []
    for report in reports:
        if report.skipped:
            continue
        val_metric = report.metrics_by_split.get("validation")
        test_metric = report.metrics_by_split.get("test")
        entries.append(
            ModelComparisonEntry(
                model_id=report.model_id,
                family=report.family,
                primary_metric_name=primary_name,
                validation_value=(
                    None if val_metric is None else metric_value(val_metric, primary_name)
                ),
                test_value=(
                    None if test_metric is None else metric_value(test_metric, primary_name)
                ),
                higher_is_better=higher_is_better,
            )
        )

    def sort_key(entry: ModelComparisonEntry) -> tuple[int, float]:
        if entry.validation_value is None:
            return (1, 0.0)
        value = entry.validation_value
        return (0, -value if higher_is_better else value)

    entries.sort(key=sort_key)
    return tuple(entries)


def _run_signature(request: TrainingRequest, model_ids: tuple[str, ...]) -> str:
    payload = {
        "dataset_id": request.dataset.metadata.dataset_id,
        "dataset_signature": request.dataset.metadata.signature_sha256,
        "target_label": request.target_label,
        "task_type": request.task_type.value,
        "model_ids": list(model_ids),
        "random_seed": request.config.random_seed,
        "fallback_split_spec": {
            "train_fraction": request.config.fallback_split_spec.train_fraction,
            "validation_fraction": request.config.fallback_split_spec.validation_fraction,
            "test_fraction": request.config.fallback_split_spec.test_fraction,
            "gap_bars": request.config.fallback_split_spec.gap_bars,
        },
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def train_and_evaluate(request: TrainingRequest) -> TrainingRunArtifact:
    model_specs = resolve_model_specs(request)
    table = _table_from_request(request)
    table, kept_names, dropped_names = _drop_zero_variance_features(table)

    reports: list[ModelEvaluationReport] = []
    run_warnings: list[str] = []
    for spec in model_specs:
        report = _fit_and_report_model(
            request=request,
            table=table,
            model_spec=spec,
        )
        reports.append(report)
        if report.skipped and report.skip_reason is not None:
            run_warnings.append(f"{report.model_id}: {report.skip_reason}")

    report_tuple = tuple(reports)
    comparison = _comparison_table(task_type=request.task_type, reports=report_tuple)
    signature = _run_signature(request, tuple(spec.model_id for spec in model_specs))
    metadata: dict[str, Any] = {
        "run_signature_sha256": signature,
        "dataset_id": request.dataset.metadata.dataset_id,
        "dataset_signature_sha256": request.dataset.metadata.signature_sha256,
        "target_label": request.target_label,
        "task_type": request.task_type.value,
        "model_count_requested": len(model_specs),
        "model_count_executed": len([r for r in report_tuple if not r.skipped]),
        "random_seed": request.config.random_seed,
        "feature_count_input": len(request.dataset.feature_names),
        "feature_count_used": len(kept_names),
        "dropped_zero_variance_features": dropped_names,
    }
    if request.dataset.splits is None:
        metadata["split_source"] = "fallback_split_spec"
    else:
        metadata["split_source"] = "dataset_provided"

    return TrainingRunArtifact(
        target_label=request.target_label,
        task_type=request.task_type,
        model_reports=report_tuple,
        comparison_table=comparison,
        run_metadata=metadata,
        warnings=tuple(run_warnings),
    )

