"""Structured artifacts for research orchestration runs."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from backtesting import BacktestResult
from diagnostics import DiagnosticsReport
from market_data import BarInterval, Candle, Instrument
from ml_data import MLDatasetArtifact
from modeling import TaskType, TrainingRunArtifact

from .contracts import ResearchWorkflowType, RunStatus, StepStatus, ResearchStepResult


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if dataclasses.is_dataclass(value):
        return _json_safe(dataclasses.asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


@dataclass(frozen=True)
class StrategyBranchSummary:
    strategy_id: str
    total_trades: int
    total_return_pct: float
    total_net_pnl: float
    max_drawdown_pct: float
    sharpe_ratio: float | None


@dataclass(frozen=True)
class MLBranchSummary:
    target_label: str
    task_type: TaskType
    best_model_id: str | None
    primary_metric_name: str | None
    best_validation_value: float | None
    best_test_value: float | None
    model_count_executed: int
    model_count_skipped: int
    warning_count: int


@dataclass(frozen=True)
class StrategyBranchArtifact:
    strategy_id: str
    backtest_result: BacktestResult
    diagnostics_report: DiagnosticsReport
    summary: StrategyBranchSummary


@dataclass(frozen=True)
class MLBranchArtifact:
    target_label: str
    task_type: TaskType
    dataset_artifact: MLDatasetArtifact
    training_artifact: TrainingRunArtifact
    summary: MLBranchSummary


@dataclass(frozen=True)
class ResearchRunArtifact:
    run_id: str
    run_name: str
    workflow_type: ResearchWorkflowType
    status: RunStatus
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    instrument: Instrument
    interval: BarInterval
    candle_count: int
    candle_source_type: str
    historical_candles: tuple[Candle, ...] | None = None
    strategy_output: StrategyBranchArtifact | None = None
    ml_output: MLBranchArtifact | None = None
    step_results: tuple[ResearchStepResult, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_summary_dict(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "run_id": self.run_id,
            "run_name": self.run_name,
            "workflow_type": self.workflow_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_ms": self.duration_ms,
            "instrument": {
                "symbol": self.instrument.symbol,
                "asset_class": self.instrument.asset_class.value,
                "venue": self.instrument.venue,
                "quote_currency": self.instrument.quote_currency,
            },
            "interval": self.interval.value,
            "candle_count": self.candle_count,
            "candle_source_type": self.candle_source_type,
            "step_results": [
                {
                    "step_name": step.step_name,
                    "status": step.status.value,
                    "started_at": step.started_at.isoformat(),
                    "ended_at": step.ended_at.isoformat(),
                    "duration_ms": step.duration_ms,
                    "error_type": step.error_type,
                    "error_message": step.error_message,
                    "metadata": _json_safe(step.metadata),
                }
                for step in self.step_results
            ],
            "metadata": _json_safe(self.metadata),
        }
        if self.historical_candles:
            summary["candle_time_range"] = {
                "start": self.historical_candles[0].timestamp.isoformat(),
                "end": self.historical_candles[-1].timestamp.isoformat(),
            }
        if self.strategy_output is not None:
            strategy_summary = self.strategy_output.summary
            summary["strategy"] = {
                "strategy_id": strategy_summary.strategy_id,
                "total_trades": strategy_summary.total_trades,
                "total_return_pct": strategy_summary.total_return_pct,
                "total_net_pnl": strategy_summary.total_net_pnl,
                "max_drawdown_pct": strategy_summary.max_drawdown_pct,
                "sharpe_ratio": strategy_summary.sharpe_ratio,
            }
        if self.ml_output is not None:
            ml_summary = self.ml_output.summary
            summary["ml"] = {
                "target_label": ml_summary.target_label,
                "task_type": ml_summary.task_type.value,
                "best_model_id": ml_summary.best_model_id,
                "primary_metric_name": ml_summary.primary_metric_name,
                "best_validation_value": ml_summary.best_validation_value,
                "best_test_value": ml_summary.best_test_value,
                "model_count_executed": ml_summary.model_count_executed,
                "model_count_skipped": ml_summary.model_count_skipped,
                "warning_count": ml_summary.warning_count,
            }
        return summary

    def to_detail_dict(self) -> dict[str, Any]:
        detail: dict[str, Any] = {
            "summary": self.to_summary_dict(),
            "strategy_detail": None,
            "ml_detail": None,
        }
        if self.strategy_output is not None:
            detail["strategy_detail"] = self._serialize_strategy_detail()
        if self.ml_output is not None:
            detail["ml_detail"] = self._serialize_ml_detail()
        return detail

    def _serialize_strategy_detail(self) -> dict[str, Any]:
        assert self.strategy_output is not None
        backtest = self.strategy_output.backtest_result
        report = self.strategy_output.diagnostics_report
        trades = [
            {
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": trade.exit_time.isoformat(),
                "direction": trade.direction.value,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "units": trade.units,
                "gross_pnl": trade.gross_pnl,
                "net_pnl": trade.net_pnl,
                "return_pct": trade.return_pct,
                "bars_held": trade.bars_held,
                "exit_reason": trade.exit_reason.value,
            }
            for trade in backtest.trades
        ]
        equity_curve = [
            {
                "timestamp": point.timestamp.isoformat(),
                "equity": point.equity,
                "cash": point.cash,
                "unrealized_pnl": point.unrealized_pnl,
                "drawdown_pct": point.drawdown_pct,
            }
            for point in report.series.equity_curve
        ]
        drawdown_curve = [
            {
                "timestamp": point.timestamp.isoformat(),
                "drawdown_pct": point.drawdown_pct,
            }
            for point in report.series.drawdown_series
        ]
        return {
            "backtest_summary": _json_safe(backtest.summary),
            "performance": _json_safe(report.performance),
            "trade_analysis": _json_safe(report.trade_analysis),
            "risk": _json_safe(report.risk),
            "assumptions": _json_safe(report.assumptions),
            "equity_curve": equity_curve,
            "drawdown_curve": drawdown_curve,
            "trades": trades,
            "drawdown_episodes": _json_safe(report.drawdown_episodes),
        }

    def _serialize_ml_detail(self) -> dict[str, Any]:
        assert self.ml_output is not None
        dataset = self.ml_output.dataset_artifact
        training = self.ml_output.training_artifact
        model_reports = []
        for report in training.model_reports:
            feature_importance = (
                None
                if report.feature_importance is None
                else [
                    {"feature": name, "score": score}
                    for name, score in report.feature_importance
                ]
            )
            model_reports.append(
                {
                    "model_id": report.model_id,
                    "family": report.family.value,
                    "task_type": report.task_type.value,
                    "skipped": report.skipped,
                    "skip_reason": report.skip_reason,
                    "metrics_by_split": _json_safe(report.metrics_by_split),
                    "feature_importance": feature_importance,
                    "warnings": _json_safe(report.warnings),
                }
            )
        return {
            "target_label": self.ml_output.target_label,
            "task_type": self.ml_output.task_type.value,
            "dataset_metadata": _json_safe(dataset.metadata),
            "comparison_table": _json_safe(training.comparison_table),
            "model_reports": model_reports,
            "run_metadata": _json_safe(training.run_metadata),
            "warnings": _json_safe(training.warnings),
        }


def build_strategy_summary(*, strategy_id: str, backtest_result: BacktestResult) -> StrategyBranchSummary:
    s = backtest_result.summary
    return StrategyBranchSummary(
        strategy_id=strategy_id,
        total_trades=s.total_trades,
        total_return_pct=s.total_return_pct,
        total_net_pnl=s.total_net_pnl,
        max_drawdown_pct=s.max_drawdown_pct,
        sharpe_ratio=s.sharpe_ratio,
    )


def build_ml_summary(*, target_label: str, task_type: TaskType, training_artifact: TrainingRunArtifact) -> MLBranchSummary:
    best = training_artifact.comparison_table[0] if training_artifact.comparison_table else None
    executed = len([r for r in training_artifact.model_reports if not r.skipped])
    skipped = len([r for r in training_artifact.model_reports if r.skipped])
    return MLBranchSummary(
        target_label=target_label,
        task_type=task_type,
        best_model_id=(None if best is None else best.model_id),
        primary_metric_name=(None if best is None else best.primary_metric_name),
        best_validation_value=(None if best is None else best.validation_value),
        best_test_value=(None if best is None else best.test_value),
        model_count_executed=executed,
        model_count_skipped=skipped,
        warning_count=len(training_artifact.warnings),
    )


def has_failed_steps(step_results: tuple[ResearchStepResult, ...]) -> bool:
    return any(step.status == StepStatus.FAILED for step in step_results)
