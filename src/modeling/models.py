"""Model registry and baseline model implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .contracts import ModelFamily, ModelSpec, TaskType


class OptionalDependencyUnavailableError(RuntimeError):
    pass


class UnsupportedModelTaskError(ValueError):
    pass


class TrainableModel(Protocol):
    uses_scaling: bool

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        ...

    def predict_scores(self, X: np.ndarray) -> np.ndarray | None:
        ...

    def feature_importance(
        self, feature_names: tuple[str, ...]
    ) -> tuple[tuple[str, float], ...] | None:
        ...


REGRESSION_FAMILIES = {
    ModelFamily.DUMMY_REGRESSOR,
    ModelFamily.RIDGE_REGRESSOR_NUMPY,
    ModelFamily.LINEAR_REGRESSION_SKLEARN,
    ModelFamily.RANDOM_FOREST_REGRESSOR_SKLEARN,
    ModelFamily.GRADIENT_BOOSTING_REGRESSOR_SKLEARN,
}

CLASSIFICATION_FAMILIES = {
    ModelFamily.DUMMY_CLASSIFIER,
    ModelFamily.LOGISTIC_REGRESSION_SKLEARN,
    ModelFamily.RANDOM_FOREST_CLASSIFIER_SKLEARN,
    ModelFamily.GRADIENT_BOOSTING_CLASSIFIER_SKLEARN,
}

OPTIONAL_DEPENDENCY_FAMILIES = {
    ModelFamily.LINEAR_REGRESSION_SKLEARN,
    ModelFamily.LOGISTIC_REGRESSION_SKLEARN,
    ModelFamily.RANDOM_FOREST_REGRESSOR_SKLEARN,
    ModelFamily.RANDOM_FOREST_CLASSIFIER_SKLEARN,
    ModelFamily.GRADIENT_BOOSTING_REGRESSOR_SKLEARN,
    ModelFamily.GRADIENT_BOOSTING_CLASSIFIER_SKLEARN,
}

LINEAR_LIKE_FAMILIES = {
    ModelFamily.RIDGE_REGRESSOR_NUMPY,
    ModelFamily.LINEAR_REGRESSION_SKLEARN,
    ModelFamily.LOGISTIC_REGRESSION_SKLEARN,
}


def model_supports_task(family: ModelFamily, task_type: TaskType) -> bool:
    if task_type == TaskType.REGRESSION:
        return family in REGRESSION_FAMILIES
    if task_type == TaskType.CLASSIFICATION:
        return family in CLASSIFICATION_FAMILIES
    return False


def is_optional_family(family: ModelFamily) -> bool:
    return family in OPTIONAL_DEPENDENCY_FAMILIES


def is_linear_like_family(family: ModelFamily) -> bool:
    return family in LINEAR_LIKE_FAMILIES


@dataclass
class DummyRegressorModel:
    uses_scaling: bool = False
    constant_: float | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        del X
        self.constant_ = float(np.mean(y))

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.constant_ is None:
            raise RuntimeError("Model is not fitted")
        return np.full(shape=(X.shape[0],), fill_value=self.constant_, dtype=float)

    def predict_scores(self, X: np.ndarray) -> np.ndarray | None:
        del X
        return None

    def feature_importance(
        self, feature_names: tuple[str, ...]
    ) -> tuple[tuple[str, float], ...] | None:
        del feature_names
        return None


@dataclass
class DummyClassifierModel:
    uses_scaling: bool = False
    majority_class_: int | None = None
    positive_class_probability_: float | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        del X
        classes, counts = np.unique(y.astype(int), return_counts=True)
        if len(classes) == 0:
            raise ValueError("DummyClassifierModel.fit received empty y")
        majority_index = int(np.argmax(counts))
        self.majority_class_ = int(classes[majority_index])
        if len(classes) == 2 and 1 in classes:
            pos_idx = int(np.where(classes == 1)[0][0])
            self.positive_class_probability_ = float(counts[pos_idx] / np.sum(counts))
        else:
            self.positive_class_probability_ = None

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.majority_class_ is None:
            raise RuntimeError("Model is not fitted")
        return np.full(shape=(X.shape[0],), fill_value=self.majority_class_, dtype=int)

    def predict_scores(self, X: np.ndarray) -> np.ndarray | None:
        if self.positive_class_probability_ is None:
            return None
        return np.full(
            shape=(X.shape[0],),
            fill_value=self.positive_class_probability_,
            dtype=float,
        )

    def feature_importance(
        self, feature_names: tuple[str, ...]
    ) -> tuple[tuple[str, float], ...] | None:
        del feature_names
        return None


@dataclass
class RidgeRegressorNumpyModel:
    alpha: float = 1.0
    uses_scaling: bool = True
    coef_: np.ndarray | None = None
    intercept_: float | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        if self.alpha < 0:
            raise ValueError("Ridge alpha must be >= 0")
        X_design = np.concatenate([np.ones((X.shape[0], 1), dtype=float), X], axis=1)
        xtx = X_design.T @ X_design
        reg = np.eye(xtx.shape[0], dtype=float) * float(self.alpha)
        reg[0, 0] = 0.0  # do not regularize intercept
        xty = X_design.T @ y
        beta = np.linalg.pinv(xtx + reg) @ xty
        self.intercept_ = float(beta[0])
        self.coef_ = beta[1:]

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.coef_ is None or self.intercept_ is None:
            raise RuntimeError("Model is not fitted")
        return (X @ self.coef_) + self.intercept_

    def predict_scores(self, X: np.ndarray) -> np.ndarray | None:
        del X
        return None

    def feature_importance(
        self, feature_names: tuple[str, ...]
    ) -> tuple[tuple[str, float], ...] | None:
        if self.coef_ is None:
            return None
        pairs = list(zip(feature_names, np.abs(self.coef_), strict=True))
        pairs.sort(key=lambda item: item[1], reverse=True)
        return tuple((name, float(value)) for name, value in pairs)


class SklearnModelWrapper:
    def __init__(self, estimator, *, uses_scaling: bool) -> None:  # noqa: ANN001
        self._estimator = estimator
        self.uses_scaling = uses_scaling

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._estimator.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self._estimator.predict(X))

    def predict_scores(self, X: np.ndarray) -> np.ndarray | None:
        if hasattr(self._estimator, "predict_proba"):
            probs = np.asarray(self._estimator.predict_proba(X))
            if probs.ndim == 2 and probs.shape[1] >= 2:
                classes = getattr(self._estimator, "classes_", None)
                if classes is not None and 1 in classes:
                    idx = int(np.where(classes == 1)[0][0])
                    return probs[:, idx]
                return probs[:, -1]
        if hasattr(self._estimator, "decision_function"):
            scores = np.asarray(self._estimator.decision_function(X))
            if scores.ndim == 1:
                return scores
        return None

    def feature_importance(
        self, feature_names: tuple[str, ...]
    ) -> tuple[tuple[str, float], ...] | None:
        if hasattr(self._estimator, "feature_importances_"):
            values = np.asarray(self._estimator.feature_importances_)
        elif hasattr(self._estimator, "coef_"):
            coef = np.asarray(self._estimator.coef_)
            values = np.mean(np.abs(coef), axis=0) if coef.ndim == 2 else np.abs(coef)
        else:
            return None

        pairs = list(zip(feature_names, values, strict=True))
        pairs.sort(key=lambda item: float(item[1]), reverse=True)
        return tuple((name, float(value)) for name, value in pairs)


def _sklearn_estimator_for_family(
    family: ModelFamily,
    hyperparameters,
    random_seed: int,
):  # noqa: ANN001
    try:
        from sklearn.ensemble import (
            GradientBoostingClassifier,
            GradientBoostingRegressor,
            RandomForestClassifier,
            RandomForestRegressor,
        )
        from sklearn.linear_model import LinearRegression, LogisticRegression
    except ModuleNotFoundError as exc:
        raise OptionalDependencyUnavailableError(
            "Optional dependency unavailable: scikit-learn is not installed"
        ) from exc

    if family == ModelFamily.LINEAR_REGRESSION_SKLEARN:
        return LinearRegression(**dict(hyperparameters))
    if family == ModelFamily.LOGISTIC_REGRESSION_SKLEARN:
        params = {"random_state": random_seed, "solver": "lbfgs"}
        params.update(dict(hyperparameters))
        return LogisticRegression(**params)
    if family == ModelFamily.RANDOM_FOREST_REGRESSOR_SKLEARN:
        params = {"random_state": random_seed}
        params.update(dict(hyperparameters))
        return RandomForestRegressor(**params)
    if family == ModelFamily.RANDOM_FOREST_CLASSIFIER_SKLEARN:
        params = {"random_state": random_seed}
        params.update(dict(hyperparameters))
        return RandomForestClassifier(**params)
    if family == ModelFamily.GRADIENT_BOOSTING_REGRESSOR_SKLEARN:
        params = {"random_state": random_seed}
        params.update(dict(hyperparameters))
        return GradientBoostingRegressor(**params)
    if family == ModelFamily.GRADIENT_BOOSTING_CLASSIFIER_SKLEARN:
        params = {"random_state": random_seed}
        params.update(dict(hyperparameters))
        return GradientBoostingClassifier(**params)
    raise ValueError(f"Unsupported sklearn model family: {family}")


def create_model(
    spec: ModelSpec,
    *,
    task_type: TaskType,
    random_seed: int,
) -> TrainableModel:
    if not model_supports_task(spec.family, task_type):
        raise UnsupportedModelTaskError(
            f"Model family '{spec.family.value}' does not support task '{task_type.value}'"
        )

    if spec.family == ModelFamily.DUMMY_REGRESSOR:
        return DummyRegressorModel()
    if spec.family == ModelFamily.DUMMY_CLASSIFIER:
        return DummyClassifierModel()
    if spec.family == ModelFamily.RIDGE_REGRESSOR_NUMPY:
        alpha = float(spec.hyperparameters.get("alpha", 1.0))
        return RidgeRegressorNumpyModel(alpha=alpha)

    estimator = _sklearn_estimator_for_family(
        spec.family,
        spec.hyperparameters,
        random_seed,
    )
    return SklearnModelWrapper(
        estimator=estimator,
        uses_scaling=is_linear_like_family(spec.family),
    )

