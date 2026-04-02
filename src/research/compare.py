"""Run comparison helpers for strategy and ML research artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

from persistence.errors import PersistenceUnavailableError
from persistence.research_runs import ResearchRunMetadataRepository
from .history import load_saved_run_bundle
from .persisted_models import CompareMetricCard, LoadedSavedRunBundle, MLCompareRow, StrategyCompareRow

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompareRunsResult:
    mode: str
    warnings: tuple[str, ...]
    cards: tuple[CompareMetricCard, ...]
    rows: tuple[StrategyCompareRow | MLCompareRow, ...]


def _mode_for_bundles(mode: str, bundles: list[LoadedSavedRunBundle]) -> str:
    if mode in {"strategy", "ml"}:
        return mode
    has_strategy = all(bundle.summary.strategy is not None for bundle in bundles)
    has_ml = all(bundle.summary.ml is not None for bundle in bundles)
    if has_strategy:
        return "strategy"
    if has_ml:
        return "ml"
    raise ValueError("Auto compare requires runs with a common comparable branch")


def _numeric(values: list[tuple[str, float | None]], prefer: str) -> CompareMetricCard:
    filtered = [(run_id, value) for run_id, value in values if value is not None]
    if not filtered:
        return CompareMetricCard(label="", direction="")
    reverse = prefer == "max"
    ordered = sorted(filtered, key=lambda item: item[1], reverse=reverse)
    best = ordered[0]
    worst = ordered[-1]
    return CompareMetricCard(
        label="",
        direction="",
        best_run_id=best[0],
        best_value=best[1],
        worst_run_id=worst[0],
        worst_value=worst[1],
    )


def _with_label(card: CompareMetricCard, *, label: str, direction: str) -> CompareMetricCard:
    return CompareMetricCard(
        label=label,
        direction=direction,
        best_run_id=card.best_run_id,
        best_value=card.best_value,
        worst_run_id=card.worst_run_id,
        worst_value=card.worst_value,
    )


def _strategy_compare(run_ids: list[str], bundles: list[LoadedSavedRunBundle]) -> CompareRunsResult:
    rows: list[StrategyCompareRow] = []
    ret_values: list[tuple[str, float | None]] = []
    dd_values: list[tuple[str, float | None]] = []
    sharpe_values: list[tuple[str, float | None]] = []
    trades_values: list[tuple[str, float | None]] = []
    for run_id, bundle in zip(run_ids, bundles, strict=True):
        summary = bundle.summary
        strategy = summary.strategy
        assert strategy is not None
        total_return = strategy.total_return_pct
        max_drawdown = strategy.max_drawdown_pct
        sharpe = strategy.sharpe_ratio
        trades = strategy.total_trades
        ret_values.append((run_id, None if total_return is None else float(total_return)))
        dd_values.append((run_id, None if max_drawdown is None else float(max_drawdown)))
        sharpe_values.append((run_id, None if sharpe is None else float(sharpe)))
        trades_values.append((run_id, None if trades is None else float(trades)))
        rows.append(
            StrategyCompareRow(
                run_id=run_id,
                run_name=summary.run_name,
                workflow_type=summary.workflow_type,
                status=summary.status,
                instrument_symbol=summary.instrument.symbol,
                interval=summary.interval,
                total_return_pct=total_return,
                max_drawdown_pct=max_drawdown,
                sharpe_ratio=sharpe,
                total_trades=trades,
                total_net_pnl=strategy.total_net_pnl,
            )
        )
    cards = (
        _with_label(_numeric(ret_values, "max"), label="Total Return %", direction="higher_is_better"),
        _with_label(_numeric(dd_values, "min"), label="Max Drawdown %", direction="lower_is_better"),
        _with_label(_numeric(sharpe_values, "max"), label="Sharpe Ratio", direction="higher_is_better"),
        _with_label(_numeric(trades_values, "max"), label="Total Trades", direction="higher_is_better"),
    )
    return CompareRunsResult(mode="strategy", warnings=(), cards=cards, rows=tuple(rows))


def _ml_compare(run_ids: list[str], bundles: list[LoadedSavedRunBundle]) -> CompareRunsResult:
    rows: list[MLCompareRow] = []
    warnings: list[str] = []
    validation_values: list[tuple[str, float | None]] = []
    test_values: list[tuple[str, float | None]] = []
    executed_values: list[tuple[str, float | None]] = []
    task_types = {None if bundle.summary.ml is None else bundle.summary.ml.task_type for bundle in bundles}
    if len(task_types - {None}) > 1:
        raise ValueError("ML compare requires the same task_type across selected runs")
    for run_id, bundle in zip(run_ids, bundles, strict=True):
        summary = bundle.summary
        ml = summary.ml
        assert ml is not None
        validation_values.append((run_id, None if ml.best_validation_value is None else float(ml.best_validation_value)))
        test_values.append((run_id, None if ml.best_test_value is None else float(ml.best_test_value)))
        executed_values.append((run_id, float(ml.model_count_executed)))
        if ml.primary_metric_name is None:
            warnings.append(f"{run_id}:missing_primary_metric_name")
        rows.append(
            MLCompareRow(
                run_id=run_id,
                run_name=summary.run_name,
                workflow_type=summary.workflow_type,
                status=summary.status,
                instrument_symbol=summary.instrument.symbol,
                interval=summary.interval,
                task_type=ml.task_type,
                target_label=ml.target_label,
                best_model_id=ml.best_model_id,
                primary_metric_name=ml.primary_metric_name,
                best_validation_value=ml.best_validation_value,
                best_test_value=ml.best_test_value,
                model_count_executed=ml.model_count_executed,
                model_count_skipped=ml.model_count_skipped,
            )
        )
    cards = (
        _with_label(
            _numeric(validation_values, "max"),
            label="Best Validation",
            direction="higher_is_better",
        ),
        _with_label(
            _numeric(test_values, "max"),
            label="Best Test",
            direction="higher_is_better",
        ),
        _with_label(
            _numeric(executed_values, "max"),
            label="Executed Models",
            direction="higher_is_better",
        ),
    )
    return CompareRunsResult(mode="ml", warnings=tuple(warnings), cards=cards, rows=tuple(rows))


def compare_saved_runs(
    *,
    root_dir: Path,
    run_ids: list[str],
    mode: str = "auto",
    metadata_repository: ResearchRunMetadataRepository | None = None,
) -> CompareRunsResult:
    unique_ids: list[str] = []
    for run_id in run_ids:
        if run_id not in unique_ids:
            unique_ids.append(run_id)
    if len(unique_ids) < 2 or len(unique_ids) > 5:
        raise ValueError("compare requires between 2 and 5 unique run_ids")

    warnings: list[str] = []
    metadata_by_id = {}
    if metadata_repository is not None:
        try:
            for run_id in unique_ids:
                metadata = metadata_repository.get_run_metadata(run_id)
                if metadata is not None:
                    metadata_by_id[run_id] = metadata
        except PersistenceUnavailableError as exc:
            LOGGER.warning(
                "Research metadata DB unavailable during compare; falling back to artifacts. %s",
                exc,
            )
            warnings.append("db_metadata_unavailable_fallback")
            metadata_by_id = {}

    bundles = [
        load_saved_run_bundle(root_dir, run_id, metadata=metadata_by_id.get(run_id))
        for run_id in unique_ids
    ]
    resolved_mode = _mode_for_bundles(mode, bundles)
    missing_rows = [
        bundle.summary.run_id
        for bundle in bundles
        if getattr(bundle.summary, resolved_mode) is None
    ]
    if missing_rows:
        raise ValueError(
            f"Selected runs are not compatible for {resolved_mode} compare: {', '.join(missing_rows)}"
        )

    if resolved_mode == "strategy":
        result = _strategy_compare(unique_ids, bundles)
    else:
        result = _ml_compare(unique_ids, bundles)
    if any(bundle.summary.interval != bundles[0].summary.interval for bundle in bundles[1:]):
        return CompareRunsResult(
            mode=result.mode,
            warnings=tuple(warnings) + result.warnings + ("interval_mismatch",),
            cards=result.cards,
            rows=result.rows,
        )
    return CompareRunsResult(
        mode=result.mode,
        warnings=tuple(warnings) + result.warnings,
        cards=result.cards,
        rows=result.rows,
    )
