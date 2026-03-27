"""Configuration helpers for model training requests."""

from __future__ import annotations

from .contracts import ModelFamily, ModelSpec, TaskType, TrainingRequest


def default_model_specs(task_type: TaskType) -> tuple[ModelSpec, ...]:
    if task_type == TaskType.REGRESSION:
        return (
            ModelSpec(model_id="dummy_regressor", family=ModelFamily.DUMMY_REGRESSOR),
            ModelSpec(
                model_id="ridge_regressor_np",
                family=ModelFamily.RIDGE_REGRESSOR_NUMPY,
                hyperparameters={"alpha": 1.0},
            ),
            ModelSpec(
                model_id="linear_regression_sklearn",
                family=ModelFamily.LINEAR_REGRESSION_SKLEARN,
                requires_optional_dependency=True,
            ),
            ModelSpec(
                model_id="random_forest_regressor_sklearn",
                family=ModelFamily.RANDOM_FOREST_REGRESSOR_SKLEARN,
                requires_optional_dependency=True,
                hyperparameters={"n_estimators": 100, "max_depth": None},
            ),
            ModelSpec(
                model_id="gradient_boosting_regressor_sklearn",
                family=ModelFamily.GRADIENT_BOOSTING_REGRESSOR_SKLEARN,
                requires_optional_dependency=True,
                hyperparameters={"n_estimators": 100, "learning_rate": 0.05},
            ),
        )

    if task_type == TaskType.CLASSIFICATION:
        return (
            ModelSpec(model_id="dummy_classifier", family=ModelFamily.DUMMY_CLASSIFIER),
            ModelSpec(
                model_id="logistic_regression_sklearn",
                family=ModelFamily.LOGISTIC_REGRESSION_SKLEARN,
                requires_optional_dependency=True,
                hyperparameters={"max_iter": 500},
            ),
            ModelSpec(
                model_id="random_forest_classifier_sklearn",
                family=ModelFamily.RANDOM_FOREST_CLASSIFIER_SKLEARN,
                requires_optional_dependency=True,
                hyperparameters={"n_estimators": 100, "max_depth": None},
            ),
            ModelSpec(
                model_id="gradient_boosting_classifier_sklearn",
                family=ModelFamily.GRADIENT_BOOSTING_CLASSIFIER_SKLEARN,
                requires_optional_dependency=True,
                hyperparameters={"n_estimators": 100, "learning_rate": 0.05},
            ),
        )

    raise ValueError(f"Unsupported task type: {task_type}")


def resolve_model_specs(request: TrainingRequest) -> tuple[ModelSpec, ...]:
    model_specs = request.model_specs or default_model_specs(request.task_type)
    seen_ids: set[str] = set()
    for spec in model_specs:
        if spec.model_id in seen_ids:
            raise ValueError(f"Duplicate model_id in request: {spec.model_id}")
        seen_ids.add(spec.model_id)
    return model_specs

