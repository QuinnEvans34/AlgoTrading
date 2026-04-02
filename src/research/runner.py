"""Research workflow runner that orchestrates strategy and ML branches."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Callable, Mapping

from market_data import Candle
from market_data.service import MarketDataService
from persistence.errors import PersistenceUnavailableError
from persistence.research_runs import (
    METADATA_SOURCE_DUAL_WRITE,
    ResearchRunMetadataRepository,
    build_run_metadata_record,
)

from .artifacts import (
    MLBranchArtifact,
    ResearchRunArtifact,
    StrategyBranchArtifact,
    build_ml_summary,
    build_strategy_summary,
    has_failed_steps,
)
from .config import detail_output_path, resolve_run_config, summary_output_path
from .contracts import (
    CandleSourceType,
    InlineCandleSource,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchStepResult,
    ResearchWorkflowType,
    RunStatus,
    StepStatus,
)
from .history import load_persisted_run_manifest
from .storage import manifest_path_for_run, persist_run_with_index
from .validation import validate_request
from .workflows import (
    resolve_candles,
    run_ml_dataset_build,
    run_model_training,
    run_strategy_backtest,
    run_strategy_diagnostics,
)


LOGGER = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _step_result(
    *,
    step_name: str,
    status: StepStatus,
    started_at: datetime,
    ended_at: datetime,
    error_type: str | None = None,
    error_message: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ResearchStepResult:
    duration_ms = int((ended_at - started_at).total_seconds() * 1000)
    return ResearchStepResult(
        step_name=step_name,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=max(0, duration_ms),
        error_type=error_type,
        error_message=error_message,
        metadata={} if metadata is None else dict(metadata),
    )


def _compute_run_status(
    *,
    strict_failures: bool,
    step_results: tuple[ResearchStepResult, ...],
    strategy_output: StrategyBranchArtifact | None,
    ml_output: MLBranchArtifact | None,
) -> RunStatus:
    if not has_failed_steps(step_results):
        return RunStatus.SUCCESS
    if strict_failures:
        return RunStatus.FAILED
    if strategy_output is None and ml_output is None:
        return RunStatus.FAILED
    return RunStatus.PARTIAL_FAILURE


class ResearchRunner:
    def __init__(
        self,
        *,
        market_data_service: MarketDataService | None = None,
        metadata_repository: ResearchRunMetadataRepository | None = None,
    ) -> None:
        self._market_data_service = market_data_service
        self._metadata_repository = metadata_repository

    def run(self, request: ResearchRunRequest) -> ResearchRunArtifact:
        validate_request(request)
        cfg = resolve_run_config(request.run_config)
        started_at = _utcnow()
        step_results: list[ResearchStepResult] = []
        metadata_overrides: dict[str, Any] = {}
        candles: tuple[Candle, ...] = ()
        source_meta: dict[str, Any] = {}
        strategy_output: StrategyBranchArtifact | None = None
        ml_output: MLBranchArtifact | None = None

        def build(status: RunStatus) -> ResearchRunArtifact:
            return self._build_artifact(
                request=request,
                config=cfg,
                started_at=started_at,
                step_results=tuple(step_results),
                candles=candles,
                candle_source_meta=source_meta,
                strategy_output=strategy_output,
                ml_output=ml_output,
                status=status,
                metadata_overrides=metadata_overrides,
            )

        resolved, error = self._run_step(
            step_results,
            "resolve_candles",
            lambda: resolve_candles(
                candle_source=request.candle_source,
                instrument=request.instrument,
                interval=request.interval,
                market_data_service=self._market_data_service,
            ),
        )
        if error is not None and cfg.strict_failures:
            return build(RunStatus.FAILED)
        if error is None:
            candles, source_meta = resolved

        if (
            request.workflow_type in (ResearchWorkflowType.STRATEGY_RESEARCH, ResearchWorkflowType.HYBRID_RESEARCH)
            and candles
            and request.strategy_spec is not None
        ):
            bt, bt_error = self._run_step(
                step_results,
                "strategy_backtest",
                lambda: run_strategy_backtest(
                    candles=candles,
                    instrument=request.instrument,
                    interval=request.interval,
                    strategy_spec=request.strategy_spec,
                ),
            )
            if bt_error is not None and cfg.strict_failures:
                return build(RunStatus.FAILED)
            if bt_error is not None:
                now = _utcnow()
                step_results.append(_step_result(step_name="strategy_diagnostics", status=StepStatus.SKIPPED, started_at=now, ended_at=now, metadata={"reason": "strategy_backtest_failed"}))
            else:
                backtest_result, strategy_name = bt
                report, diag_error = self._run_step(
                    step_results,
                    "strategy_diagnostics",
                    lambda: run_strategy_diagnostics(
                        backtest_result=backtest_result,
                        strategy_spec=request.strategy_spec,
                        run_id=cfg.run_id or "unknown-run",
                        run_name=cfg.run_name or "unknown-run",
                    ),
                )
                if diag_error is not None and cfg.strict_failures:
                    return build(RunStatus.FAILED)
                if diag_error is None:
                    strategy_output = StrategyBranchArtifact(
                        strategy_id=strategy_name,
                        backtest_result=backtest_result,
                        diagnostics_report=report,
                        summary=build_strategy_summary(strategy_id=strategy_name, backtest_result=backtest_result),
                    )

        if (
            request.workflow_type in (ResearchWorkflowType.ML_RESEARCH, ResearchWorkflowType.HYBRID_RESEARCH)
            and candles
            and request.ml_spec is not None
        ):
            dataset, ds_error = self._run_step(
                step_results,
                "ml_dataset_build",
                lambda: run_ml_dataset_build(
                    candles=candles,
                    instrument=request.instrument,
                    interval=request.interval,
                    ml_spec=request.ml_spec,
                ),
            )
            if ds_error is not None and cfg.strict_failures:
                return build(RunStatus.FAILED)
            if ds_error is not None:
                now = _utcnow()
                step_results.append(_step_result(step_name="ml_model_training", status=StepStatus.SKIPPED, started_at=now, ended_at=now, metadata={"reason": "ml_dataset_build_failed"}))
            else:
                training, tr_error = self._run_step(
                    step_results,
                    "ml_model_training",
                    lambda: run_model_training(dataset=dataset, ml_spec=request.ml_spec, run_seed=cfg.random_seed),
                )
                if tr_error is not None and cfg.strict_failures:
                    return build(RunStatus.FAILED)
                if tr_error is None:
                    training_artifact, target_label = training
                    ml_output = MLBranchArtifact(
                        target_label=target_label,
                        task_type=request.ml_spec.task_type,
                        dataset_artifact=dataset,
                        training_artifact=training_artifact,
                        summary=build_ml_summary(
                            target_label=target_label,
                            task_type=request.ml_spec.task_type,
                            training_artifact=training_artifact,
                        ),
                    )

        candidate = build(_compute_run_status(strict_failures=cfg.strict_failures, step_results=tuple(step_results), strategy_output=strategy_output, ml_output=ml_output))
        if cfg.persist_summary:
            persist_start = _utcnow()
            try:
                output_paths = self._persist_artifacts(candidate, cfg)
                metadata_overrides["summary_output_path"] = str(output_paths["summary"])
                metadata_overrides["detail_output_path"] = str(output_paths["detail"])
                metadata_overrides["manifest_output_path"] = str(output_paths["manifest"])
                metadata_overrides["index_output_path"] = str(output_paths["index"])
                step_results.append(
                    _step_result(
                        step_name="persist_summary",
                        status=StepStatus.SUCCESS,
                        started_at=persist_start,
                        ended_at=_utcnow(),
                        metadata={
                            "summary_output_path": str(output_paths["summary"]),
                            "detail_output_path": str(output_paths["detail"]),
                            "manifest_output_path": str(output_paths["manifest"]),
                            "index_output_path": str(output_paths["index"]),
                        },
                    )
                )
            except Exception as exc:  # noqa: BLE001
                step_results.append(_step_result(step_name="persist_summary", status=StepStatus.FAILED, started_at=persist_start, ended_at=_utcnow(), error_type=type(exc).__name__, error_message=str(exc)))
                if cfg.strict_failures:
                    return build(RunStatus.FAILED)
        final_status = _compute_run_status(strict_failures=cfg.strict_failures, step_results=tuple(step_results), strategy_output=strategy_output, ml_output=ml_output)
        return build(final_status)

    def _run_step(
        self,
        step_results: list[ResearchStepResult],
        step_name: str,
        fn: Callable[[], Any],
    ) -> tuple[Any, Exception | None]:
        started = _utcnow()
        try:
            value = fn()
            step_results.append(_step_result(step_name=step_name, status=StepStatus.SUCCESS, started_at=started, ended_at=_utcnow()))
            return value, None
        except Exception as exc:  # noqa: BLE001
            step_results.append(_step_result(step_name=step_name, status=StepStatus.FAILED, started_at=started, ended_at=_utcnow(), error_type=type(exc).__name__, error_message=str(exc)))
            return None, exc

    def _persist_artifacts(
        self,
        artifact: ResearchRunArtifact,
        config: ResearchRunConfig,
    ) -> dict[str, Path]:
        summary_path = summary_output_path(config)
        detail_path = detail_output_path(config)
        if summary_path is None or detail_path is None:
            raise ValueError("persist_summary is enabled but no output path could be resolved")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(artifact.to_summary_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        detail_path.write_text(
            json.dumps(artifact.to_detail_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        root_dir = Path(config.output_dir)
        manifest, _ = persist_run_with_index(
            root_dir=root_dir,
            artifact=artifact,
            summary_path=summary_path,
            detail_path=detail_path,
        )
        self._persist_metadata_record(
            root_dir=root_dir,
            artifact=artifact,
        )
        return {
            "summary": summary_path,
            "detail": detail_path,
            "manifest": manifest_path_for_run(root_dir, manifest.run_id),
            "index": root_dir / "index.json",
        }

    def _persist_metadata_record(
        self,
        *,
        root_dir: Path,
        artifact: ResearchRunArtifact,
    ) -> None:
        if self._metadata_repository is None:
            return
        try:
            summary = artifact.to_persisted_summary()
            manifest = load_persisted_run_manifest(root_dir, artifact.run_id)
            self._metadata_repository.upsert_run_metadata(
                build_run_metadata_record(
                    root_dir=root_dir,
                    summary=summary,
                    manifest=manifest,
                    metadata_source=METADATA_SOURCE_DUAL_WRITE,
                )
            )
        except (PersistenceUnavailableError, OSError, TypeError, ValueError) as exc:
            LOGGER.warning(
                "Research metadata DB unavailable for run '%s'; keeping artifact-only persistence. %s",
                artifact.run_id,
                exc,
            )

    def _build_artifact(
        self,
        *,
        request: ResearchRunRequest,
        config: ResearchRunConfig,
        started_at: datetime,
        step_results: tuple[ResearchStepResult, ...],
        candles: tuple[Candle, ...],
        candle_source_meta: Mapping[str, Any],
        strategy_output: StrategyBranchArtifact | None,
        ml_output: MLBranchArtifact | None,
        status: RunStatus,
        metadata_overrides: Mapping[str, Any],
    ) -> ResearchRunArtifact:
        source_type = CandleSourceType.INLINE_CANDLES.value if isinstance(request.candle_source, InlineCandleSource) else CandleSourceType.MARKET_DATA_FETCH.value
        metadata: dict[str, Any] = dict(config.metadata)
        metadata["random_seed"] = config.random_seed
        metadata["strict_failures"] = config.strict_failures
        metadata["candle_source"] = dict(candle_source_meta)
        metadata.update(metadata_overrides)
        ended_at = _utcnow()
        duration_ms = int((ended_at - started_at).total_seconds() * 1000)
        return ResearchRunArtifact(
            run_id=config.run_id or "unknown-run",
            run_name=config.run_name or "unknown-run",
            workflow_type=request.workflow_type,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=max(0, duration_ms),
            instrument=request.instrument,
            interval=request.interval,
            candle_count=len(candles),
            candle_source_type=source_type,
            historical_candles=candles if candles else None,
            strategy_output=strategy_output,
            ml_output=ml_output,
            step_results=step_results,
            metadata=metadata,
        )
