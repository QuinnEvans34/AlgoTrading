# Model Training Subsystem (Baseline Training + Evaluation)

## Purpose
The modeling subsystem trains and evaluates baseline tabular models from `ml_data` artifacts.
It is research-focused, deterministic where practical, and produces structured outputs for later model comparison and diagnostics views.

## Architecture
- `src/modeling/contracts.py`
  - Core task/model/training/evaluation contracts.
- `src/modeling/config.py`
  - Default model sets and request model resolution.
- `src/modeling/models.py`
  - Model registry + implementations:
    - required numpy baselines
    - optional scikit-learn families behind dependency checks
- `src/modeling/evaluation.py`
  - Regression/classification metric calculations and primary metric helpers.
- `src/modeling/trainer.py`
  - End-to-end orchestration from dataset artifact to `TrainingRunArtifact`.
- `src/modeling/artifacts.py`
  - Structured report objects for per-model outputs and comparison-ready summaries.

## Integration Boundary
- Input: `ml_data.MLDatasetArtifact` and a chosen `target_label`.
- Output: `TrainingRunArtifact` containing:
  - per-model split metrics (`train`/`validation`/`test`)
  - split prediction bundles
  - feature-importance outputs (when supported)
  - run metadata and reproducibility signatures

No broker/provider/live-trading coupling exists in this layer.

## Models Included in This Phase
Required (no optional deps):
- `dummy_regressor`
- `dummy_classifier`
- `ridge_regressor_np` (closed-form ridge)

Optional (requires `scikit-learn`):
- linear/logistic regression
- random forest classifier/regressor
- gradient boosting classifier/regressor

If `scikit-learn` is unavailable, optional models are skipped (default policy) with explicit warnings.

## Metrics Included in This Phase
Regression:
- MAE
- RMSE
- R²
- directional accuracy (`sign(y_pred) == sign(y_true)`)

Classification:
- accuracy
- precision, recall, F1 (binary positive class path)
- balanced accuracy
- confusion matrix
- ROC AUC when score/probability output is available and binary class support is valid

## Determinism / Reproducibility
- Fixed random seed in request config.
- Train/validation/test split source is captured (`dataset_provided` or fallback split).
- Zero-variance feature removal is train-split driven and recorded.
- Run signature hash captures dataset signature, target, model IDs, and seed.

## Explicit Constraints
- Single-target training per run.
- Missing/NaN/inf in modeling inputs is a hard error.
- No model persistence/registry service in this phase.
- No hyperparameter search in this phase.
- No online inference or deployment workflows in this phase.

## Deferred to Later Phases
- experiment tracking platform
- model artifact persistence/versioning
- advanced calibration and residual packages
- auto-tuning / search workflows
- online serving and model deployment automation
- distributed training infrastructure

