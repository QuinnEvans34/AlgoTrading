"""Typed models and loaders for persisted research run artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping


LEGACY_ARTIFACT_SCHEMA_VERSION = 1


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TypeError(f"Expected JSON object in '{path}'")
    return {str(key): value for key, value in payload.items()}


def _mapping(value: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{context} must be a JSON object")
    return {str(key): item for key, item in value.items()}


def _list(value: Any, *, context: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a JSON array")
    return list(value)


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    raw = payload.get(key)
    if raw is None:
        raise ValueError(f"Missing required field '{key}'")
    return str(raw)


def _optional_str(payload: Mapping[str, Any], key: str) -> str | None:
    raw = payload.get(key)
    return None if raw is None else str(raw)


def _required_int(payload: Mapping[str, Any], key: str) -> int:
    raw = payload.get(key)
    if raw is None:
        raise ValueError(f"Missing required field '{key}'")
    return int(raw)


def _optional_int(payload: Mapping[str, Any], key: str) -> int | None:
    raw = payload.get(key)
    return None if raw is None else int(raw)


def _optional_float(payload: Mapping[str, Any], key: str) -> float | None:
    raw = payload.get(key)
    return None if raw is None else float(raw)


def _required_float(payload: Mapping[str, Any], key: str) -> float:
    raw = payload.get(key)
    if raw is None:
        raise ValueError(f"Missing required field '{key}'")
    return float(raw)


def _required_bool(payload: Mapping[str, Any], key: str) -> bool:
    raw = payload.get(key)
    if raw is None:
        raise ValueError(f"Missing required field '{key}'")
    return bool(raw)


def _optional_datetime(payload: Mapping[str, Any], key: str) -> datetime | None:
    raw = payload.get(key)
    if raw is None:
        return None
    return datetime.fromisoformat(str(raw))


def _required_datetime(payload: Mapping[str, Any], key: str) -> datetime:
    raw = payload.get(key)
    if raw is None:
        raise ValueError(f"Missing required field '{key}'")
    return datetime.fromisoformat(str(raw))


def _string_tuple(value: Any, *, context: str) -> tuple[str, ...]:
    return tuple(str(item) for item in _list(value, context=context))


@dataclass(frozen=True)
class PersistedInstrument:
    symbol: str
    asset_class: str
    venue: str | None = None
    quote_currency: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "asset_class": self.asset_class,
            "venue": self.venue,
            "quote_currency": self.quote_currency,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedInstrument":
        return PersistedInstrument(
            symbol=_required_str(payload, "symbol"),
            asset_class=_required_str(payload, "asset_class"),
            venue=_optional_str(payload, "venue"),
            quote_currency=_optional_str(payload, "quote_currency"),
        )


@dataclass(frozen=True)
class PersistedStepResult:
    step_name: str
    status: str
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_name": self.step_name,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_ms": self.duration_ms,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedStepResult":
        return PersistedStepResult(
            step_name=_required_str(payload, "step_name"),
            status=_required_str(payload, "status"),
            started_at=_required_datetime(payload, "started_at"),
            ended_at=_required_datetime(payload, "ended_at"),
            duration_ms=_required_int(payload, "duration_ms"),
            error_type=_optional_str(payload, "error_type"),
            error_message=_optional_str(payload, "error_message"),
            metadata=_mapping(payload.get("metadata", {}), context="step_results[].metadata"),
        )


@dataclass(frozen=True)
class PersistedCandleTimeRange:
    start: datetime
    end: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedCandleTimeRange":
        return PersistedCandleTimeRange(
            start=_required_datetime(payload, "start"),
            end=_required_datetime(payload, "end"),
        )


@dataclass(frozen=True)
class PersistedStrategySummary:
    strategy_id: str
    total_trades: int
    total_return_pct: float
    total_net_pnl: float
    max_drawdown_pct: float
    sharpe_ratio: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "total_trades": self.total_trades,
            "total_return_pct": self.total_return_pct,
            "total_net_pnl": self.total_net_pnl,
            "max_drawdown_pct": self.max_drawdown_pct,
            "sharpe_ratio": self.sharpe_ratio,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedStrategySummary":
        return PersistedStrategySummary(
            strategy_id=_required_str(payload, "strategy_id"),
            total_trades=_required_int(payload, "total_trades"),
            total_return_pct=_required_float(payload, "total_return_pct"),
            total_net_pnl=_required_float(payload, "total_net_pnl"),
            max_drawdown_pct=_required_float(payload, "max_drawdown_pct"),
            sharpe_ratio=_optional_float(payload, "sharpe_ratio"),
        )


@dataclass(frozen=True)
class PersistedMLSummary:
    target_label: str
    task_type: str
    best_model_id: str | None = None
    primary_metric_name: str | None = None
    best_validation_value: float | None = None
    best_test_value: float | None = None
    model_count_executed: int = 0
    model_count_skipped: int = 0
    warning_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_label": self.target_label,
            "task_type": self.task_type,
            "best_model_id": self.best_model_id,
            "primary_metric_name": self.primary_metric_name,
            "best_validation_value": self.best_validation_value,
            "best_test_value": self.best_test_value,
            "model_count_executed": self.model_count_executed,
            "model_count_skipped": self.model_count_skipped,
            "warning_count": self.warning_count,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedMLSummary":
        return PersistedMLSummary(
            target_label=_required_str(payload, "target_label"),
            task_type=_required_str(payload, "task_type"),
            best_model_id=_optional_str(payload, "best_model_id"),
            primary_metric_name=_optional_str(payload, "primary_metric_name"),
            best_validation_value=_optional_float(payload, "best_validation_value"),
            best_test_value=_optional_float(payload, "best_test_value"),
            model_count_executed=_required_int(payload, "model_count_executed"),
            model_count_skipped=_required_int(payload, "model_count_skipped"),
            warning_count=_required_int(payload, "warning_count"),
        )


@dataclass(frozen=True)
class PersistedRunSummary:
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    instrument: PersistedInstrument
    interval: str
    candle_count: int
    candle_source_type: str
    step_results: tuple[PersistedStepResult, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    candle_time_range: PersistedCandleTimeRange | None = None
    strategy: PersistedStrategySummary | None = None
    ml: PersistedMLSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "run_id": self.run_id,
            "run_name": self.run_name,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_ms": self.duration_ms,
            "instrument": self.instrument.to_dict(),
            "interval": self.interval,
            "candle_count": self.candle_count,
            "candle_source_type": self.candle_source_type,
            "step_results": [step.to_dict() for step in self.step_results],
            "metadata": dict(self.metadata),
        }
        if self.candle_time_range is not None:
            payload["candle_time_range"] = self.candle_time_range.to_dict()
        if self.strategy is not None:
            payload["strategy"] = self.strategy.to_dict()
        if self.ml is not None:
            payload["ml"] = self.ml.to_dict()
        return payload

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedRunSummary":
        run_id = _required_str(payload, "run_id")
        return PersistedRunSummary(
            run_id=run_id,
            run_name=str(payload.get("run_name", run_id)),
            workflow_type=str(payload.get("workflow_type", "unknown")),
            status=str(payload.get("status", "unknown")),
            started_at=_required_datetime(payload, "started_at"),
            ended_at=_required_datetime(payload, "ended_at"),
            duration_ms=_required_int(payload, "duration_ms"),
            instrument=PersistedInstrument.from_dict(
                _mapping(payload.get("instrument", {}), context="summary.instrument")
            ),
            interval=_required_str(payload, "interval"),
            candle_count=_required_int(payload, "candle_count"),
            candle_source_type=_required_str(payload, "candle_source_type"),
            step_results=tuple(
                PersistedStepResult.from_dict(_mapping(item, context="summary.step_results[]"))
                for item in _list(payload.get("step_results", []), context="summary.step_results")
            ),
            metadata=_mapping(payload.get("metadata", {}), context="summary.metadata"),
            candle_time_range=(
                None
                if payload.get("candle_time_range") is None
                else PersistedCandleTimeRange.from_dict(
                    _mapping(payload.get("candle_time_range"), context="summary.candle_time_range")
                )
            ),
            strategy=(
                None
                if payload.get("strategy") is None
                else PersistedStrategySummary.from_dict(
                    _mapping(payload.get("strategy"), context="summary.strategy")
                )
            ),
            ml=(
                None
                if payload.get("ml") is None
                else PersistedMLSummary.from_dict(_mapping(payload.get("ml"), context="summary.ml"))
            ),
        )

    @staticmethod
    def load(path: Path) -> "PersistedRunSummary":
        return PersistedRunSummary.from_dict(_read_json(path))


@dataclass(frozen=True)
class PersistedStrategyTrade:
    entry_time: datetime
    exit_time: datetime
    direction: str
    entry_price: float
    exit_price: float
    units: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    bars_held: int
    exit_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "direction": self.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "units": self.units,
            "gross_pnl": self.gross_pnl,
            "net_pnl": self.net_pnl,
            "return_pct": self.return_pct,
            "bars_held": self.bars_held,
            "exit_reason": self.exit_reason,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedStrategyTrade":
        return PersistedStrategyTrade(
            entry_time=_required_datetime(payload, "entry_time"),
            exit_time=_required_datetime(payload, "exit_time"),
            direction=_required_str(payload, "direction"),
            entry_price=_required_float(payload, "entry_price"),
            exit_price=_required_float(payload, "exit_price"),
            units=_required_float(payload, "units"),
            gross_pnl=_required_float(payload, "gross_pnl"),
            net_pnl=_required_float(payload, "net_pnl"),
            return_pct=_required_float(payload, "return_pct"),
            bars_held=_required_int(payload, "bars_held"),
            exit_reason=_required_str(payload, "exit_reason"),
        )


@dataclass(frozen=True)
class PersistedEquityPoint:
    timestamp: datetime
    equity: float
    cash: float
    unrealized_pnl: float
    drawdown_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "equity": self.equity,
            "cash": self.cash,
            "unrealized_pnl": self.unrealized_pnl,
            "drawdown_pct": self.drawdown_pct,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedEquityPoint":
        return PersistedEquityPoint(
            timestamp=_required_datetime(payload, "timestamp"),
            equity=_required_float(payload, "equity"),
            cash=_required_float(payload, "cash"),
            unrealized_pnl=_required_float(payload, "unrealized_pnl"),
            drawdown_pct=_required_float(payload, "drawdown_pct"),
        )


@dataclass(frozen=True)
class PersistedDrawdownPoint:
    timestamp: datetime
    drawdown_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "drawdown_pct": self.drawdown_pct,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedDrawdownPoint":
        return PersistedDrawdownPoint(
            timestamp=_required_datetime(payload, "timestamp"),
            drawdown_pct=_required_float(payload, "drawdown_pct"),
        )


@dataclass(frozen=True)
class PersistedDrawdownEpisode:
    peak_time: datetime
    trough_time: datetime
    recovery_time: datetime | None
    depth_pct: float
    duration_bars: int
    recovery_bars: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "peak_time": self.peak_time.isoformat(),
            "trough_time": self.trough_time.isoformat(),
            "recovery_time": None if self.recovery_time is None else self.recovery_time.isoformat(),
            "depth_pct": self.depth_pct,
            "duration_bars": self.duration_bars,
            "recovery_bars": self.recovery_bars,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedDrawdownEpisode":
        return PersistedDrawdownEpisode(
            peak_time=_required_datetime(payload, "peak_time"),
            trough_time=_required_datetime(payload, "trough_time"),
            recovery_time=_optional_datetime(payload, "recovery_time"),
            depth_pct=_required_float(payload, "depth_pct"),
            duration_bars=_required_int(payload, "duration_bars"),
            recovery_bars=_optional_int(payload, "recovery_bars"),
        )


@dataclass(frozen=True)
class PersistedStrategyDetail:
    backtest_summary: dict[str, Any]
    performance: dict[str, Any]
    trade_analysis: dict[str, Any]
    risk: dict[str, Any]
    assumptions: dict[str, Any]
    equity_curve: tuple[PersistedEquityPoint, ...]
    drawdown_curve: tuple[PersistedDrawdownPoint, ...]
    trades: tuple[PersistedStrategyTrade, ...]
    drawdown_episodes: tuple[PersistedDrawdownEpisode, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "backtest_summary": dict(self.backtest_summary),
            "performance": dict(self.performance),
            "trade_analysis": dict(self.trade_analysis),
            "risk": dict(self.risk),
            "assumptions": dict(self.assumptions),
            "equity_curve": [point.to_dict() for point in self.equity_curve],
            "drawdown_curve": [point.to_dict() for point in self.drawdown_curve],
            "trades": [trade.to_dict() for trade in self.trades],
            "drawdown_episodes": [episode.to_dict() for episode in self.drawdown_episodes],
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedStrategyDetail":
        return PersistedStrategyDetail(
            backtest_summary=_mapping(payload.get("backtest_summary", {}), context="strategy_detail.backtest_summary"),
            performance=_mapping(payload.get("performance", {}), context="strategy_detail.performance"),
            trade_analysis=_mapping(payload.get("trade_analysis", {}), context="strategy_detail.trade_analysis"),
            risk=_mapping(payload.get("risk", {}), context="strategy_detail.risk"),
            assumptions=_mapping(payload.get("assumptions", {}), context="strategy_detail.assumptions"),
            equity_curve=tuple(
                PersistedEquityPoint.from_dict(_mapping(item, context="strategy_detail.equity_curve[]"))
                for item in _list(payload.get("equity_curve", []), context="strategy_detail.equity_curve")
            ),
            drawdown_curve=tuple(
                PersistedDrawdownPoint.from_dict(_mapping(item, context="strategy_detail.drawdown_curve[]"))
                for item in _list(payload.get("drawdown_curve", []), context="strategy_detail.drawdown_curve")
            ),
            trades=tuple(
                PersistedStrategyTrade.from_dict(_mapping(item, context="strategy_detail.trades[]"))
                for item in _list(payload.get("trades", []), context="strategy_detail.trades")
            ),
            drawdown_episodes=tuple(
                PersistedDrawdownEpisode.from_dict(
                    _mapping(item, context="strategy_detail.drawdown_episodes[]")
                )
                for item in _list(
                    payload.get("drawdown_episodes", []),
                    context="strategy_detail.drawdown_episodes",
                )
            ),
        )


@dataclass(frozen=True)
class PersistedModelComparisonEntry:
    model_id: str
    family: str
    primary_metric_name: str
    validation_value: float | None
    test_value: float | None
    higher_is_better: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "family": self.family,
            "primary_metric_name": self.primary_metric_name,
            "validation_value": self.validation_value,
            "test_value": self.test_value,
            "higher_is_better": self.higher_is_better,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedModelComparisonEntry":
        return PersistedModelComparisonEntry(
            model_id=_required_str(payload, "model_id"),
            family=_required_str(payload, "family"),
            primary_metric_name=_required_str(payload, "primary_metric_name"),
            validation_value=_optional_float(payload, "validation_value"),
            test_value=_optional_float(payload, "test_value"),
            higher_is_better=_required_bool(payload, "higher_is_better"),
        )


@dataclass(frozen=True)
class PersistedFeatureImportanceItem:
    feature: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "score": self.score,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedFeatureImportanceItem":
        return PersistedFeatureImportanceItem(
            feature=_required_str(payload, "feature"),
            score=_required_float(payload, "score"),
        )


@dataclass(frozen=True)
class PersistedModelReport:
    model_id: str
    family: str
    task_type: str
    skipped: bool
    skip_reason: str | None
    metrics_by_split: dict[str, dict[str, Any]]
    feature_importance: tuple[PersistedFeatureImportanceItem, ...] | None
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "family": self.family,
            "task_type": self.task_type,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "metrics_by_split": {
                split: dict(metrics) for split, metrics in self.metrics_by_split.items()
            },
            "feature_importance": (
                None
                if self.feature_importance is None
                else [item.to_dict() for item in self.feature_importance]
            ),
            "warnings": list(self.warnings),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedModelReport":
        metrics_raw = _mapping(payload.get("metrics_by_split", {}), context="ml_detail.metrics_by_split")
        metrics = {
            split: _mapping(values, context=f"ml_detail.metrics_by_split.{split}")
            for split, values in metrics_raw.items()
        }
        raw_feature_importance = payload.get("feature_importance")
        feature_importance = None
        if raw_feature_importance is not None:
            feature_importance = tuple(
                PersistedFeatureImportanceItem.from_dict(
                    _mapping(item, context="ml_detail.feature_importance[]")
                )
                for item in _list(raw_feature_importance, context="ml_detail.feature_importance")
            )
        return PersistedModelReport(
            model_id=_required_str(payload, "model_id"),
            family=_required_str(payload, "family"),
            task_type=_required_str(payload, "task_type"),
            skipped=_required_bool(payload, "skipped"),
            skip_reason=_optional_str(payload, "skip_reason"),
            metrics_by_split=metrics,
            feature_importance=feature_importance,
            warnings=_string_tuple(payload.get("warnings", []), context="ml_detail.warnings"),
        )


@dataclass(frozen=True)
class PersistedMLDetail:
    target_label: str
    task_type: str
    dataset_metadata: dict[str, Any]
    comparison_table: tuple[PersistedModelComparisonEntry, ...]
    model_reports: tuple[PersistedModelReport, ...]
    run_metadata: dict[str, Any]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_label": self.target_label,
            "task_type": self.task_type,
            "dataset_metadata": dict(self.dataset_metadata),
            "comparison_table": [entry.to_dict() for entry in self.comparison_table],
            "model_reports": [report.to_dict() for report in self.model_reports],
            "run_metadata": dict(self.run_metadata),
            "warnings": list(self.warnings),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PersistedMLDetail":
        return PersistedMLDetail(
            target_label=_required_str(payload, "target_label"),
            task_type=_required_str(payload, "task_type"),
            dataset_metadata=_mapping(payload.get("dataset_metadata", {}), context="ml_detail.dataset_metadata"),
            comparison_table=tuple(
                PersistedModelComparisonEntry.from_dict(
                    _mapping(item, context="ml_detail.comparison_table[]")
                )
                for item in _list(payload.get("comparison_table", []), context="ml_detail.comparison_table")
            ),
            model_reports=tuple(
                PersistedModelReport.from_dict(_mapping(item, context="ml_detail.model_reports[]"))
                for item in _list(payload.get("model_reports", []), context="ml_detail.model_reports")
            ),
            run_metadata=_mapping(payload.get("run_metadata", {}), context="ml_detail.run_metadata"),
            warnings=_string_tuple(payload.get("warnings", []), context="ml_detail.warnings"),
        )


@dataclass(frozen=True)
class PersistedRunDetail:
    summary: PersistedRunSummary
    strategy_detail: PersistedStrategyDetail | None = None
    ml_detail: PersistedMLDetail | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "strategy_detail": (
                None if self.strategy_detail is None else self.strategy_detail.to_dict()
            ),
            "ml_detail": None if self.ml_detail is None else self.ml_detail.to_dict(),
        }

    @staticmethod
    def summary_only(summary: PersistedRunSummary) -> "PersistedRunDetail":
        return PersistedRunDetail(summary=summary, strategy_detail=None, ml_detail=None)

    @staticmethod
    def from_dict(
        payload: Mapping[str, Any],
        *,
        summary: PersistedRunSummary,
    ) -> "PersistedRunDetail":
        return PersistedRunDetail(
            summary=summary,
            strategy_detail=(
                None
                if payload.get("strategy_detail") is None
                else PersistedStrategyDetail.from_dict(
                    _mapping(payload.get("strategy_detail"), context="detail.strategy_detail")
                )
            ),
            ml_detail=(
                None
                if payload.get("ml_detail") is None
                else PersistedMLDetail.from_dict(
                    _mapping(payload.get("ml_detail"), context="detail.ml_detail")
                )
            ),
        )


@dataclass(frozen=True)
class PersistedManifestView:
    schema_version: int
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_ms: int | None
    instrument_symbol: str
    asset_class: str | None
    interval: str | None
    candle_count: int | None
    has_strategy: bool
    has_ml: bool
    summary_path: str
    detail_path: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    synthetic: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "run_name": self.run_name,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "started_at": None if self.started_at is None else self.started_at.isoformat(),
            "ended_at": None if self.ended_at is None else self.ended_at.isoformat(),
            "duration_ms": self.duration_ms,
            "instrument_symbol": self.instrument_symbol,
            "asset_class": self.asset_class,
            "interval": self.interval,
            "candle_count": self.candle_count,
            "has_strategy": self.has_strategy,
            "has_ml": self.has_ml,
            "summary_path": self.summary_path,
            "detail_path": self.detail_path,
            "created_at": None if self.created_at is None else self.created_at.isoformat(),
            "updated_at": None if self.updated_at is None else self.updated_at.isoformat(),
            "synthetic": self.synthetic,
        }


@dataclass(frozen=True)
class LoadedSavedRunBundle:
    summary: PersistedRunSummary
    detail: PersistedRunDetail
    manifest: PersistedManifestView


@dataclass(frozen=True)
class CompareMetricCard:
    label: str
    direction: str
    best_run_id: str | None = None
    best_value: float | None = None
    worst_run_id: str | None = None
    worst_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "direction": self.direction,
            "best_run_id": self.best_run_id,
            "best_value": self.best_value,
            "worst_run_id": self.worst_run_id,
            "worst_value": self.worst_value,
        }


@dataclass(frozen=True)
class StrategyCompareRow:
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    instrument_symbol: str
    interval: str
    total_return_pct: float | None
    max_drawdown_pct: float | None
    sharpe_ratio: float | None
    total_trades: int | None
    total_net_pnl: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_name": self.run_name,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "instrument_symbol": self.instrument_symbol,
            "interval": self.interval,
            "total_return_pct": self.total_return_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "total_trades": self.total_trades,
            "total_net_pnl": self.total_net_pnl,
        }


@dataclass(frozen=True)
class MLCompareRow:
    run_id: str
    run_name: str
    workflow_type: str
    status: str
    instrument_symbol: str
    interval: str
    task_type: str | None
    target_label: str | None
    best_model_id: str | None
    primary_metric_name: str | None
    best_validation_value: float | None
    best_test_value: float | None
    model_count_executed: int | None
    model_count_skipped: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_name": self.run_name,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "instrument_symbol": self.instrument_symbol,
            "interval": self.interval,
            "task_type": self.task_type,
            "target_label": self.target_label,
            "best_model_id": self.best_model_id,
            "primary_metric_name": self.primary_metric_name,
            "best_validation_value": self.best_validation_value,
            "best_test_value": self.best_test_value,
            "model_count_executed": self.model_count_executed,
            "model_count_skipped": self.model_count_skipped,
        }
