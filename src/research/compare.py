"""Run comparison helpers for strategy and ML research artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .history import get_run_detail, get_run_manifest


@dataclass(frozen=True)
class CompareRunsResult:
    mode: str
    warnings: tuple[str, ...]
    cards: tuple[dict[str, Any], ...]
    rows: tuple[dict[str, Any], ...]


def _mode_for_details(mode: str, details: list[dict[str, Any]]) -> str:
    if mode in {"strategy", "ml"}:
        return mode
    has_strategy = all(detail.get("strategy_detail") is not None for detail in details)
    has_ml = all(detail.get("ml_detail") is not None for detail in details)
    if has_strategy:
        return "strategy"
    if has_ml:
        return "ml"
    raise ValueError("Auto compare requires runs with a common comparable branch")


def _numeric(values: list[tuple[str, float | None]], prefer: str) -> dict[str, Any]:
    filtered = [(run_id, value) for run_id, value in values if value is not None]
    if not filtered:
        return {"best_run_id": None, "best_value": None, "worst_run_id": None, "worst_value": None}
    reverse = prefer == "max"
    ordered = sorted(filtered, key=lambda item: item[1], reverse=reverse)
    best = ordered[0]
    worst = ordered[-1]
    return {
        "best_run_id": best[0],
        "best_value": best[1],
        "worst_run_id": worst[0],
        "worst_value": worst[1],
    }


def _strategy_compare(run_ids: list[str], details: list[dict[str, Any]]) -> CompareRunsResult:
    rows: list[dict[str, Any]] = []
    ret_values: list[tuple[str, float | None]] = []
    dd_values: list[tuple[str, float | None]] = []
    sharpe_values: list[tuple[str, float | None]] = []
    trades_values: list[tuple[str, float | None]] = []
    for run_id, detail in zip(run_ids, details, strict=True):
        summary = detail.get("summary", {})
        strategy = summary.get("strategy") or {}
        total_return = strategy.get("total_return_pct")
        max_drawdown = strategy.get("max_drawdown_pct")
        sharpe = strategy.get("sharpe_ratio")
        trades = strategy.get("total_trades")
        ret_values.append((run_id, None if total_return is None else float(total_return)))
        dd_values.append((run_id, None if max_drawdown is None else float(max_drawdown)))
        sharpe_values.append((run_id, None if sharpe is None else float(sharpe)))
        trades_values.append((run_id, None if trades is None else float(trades)))
        rows.append(
            {
                "run_id": run_id,
                "run_name": summary.get("run_name"),
                "workflow_type": summary.get("workflow_type"),
                "status": summary.get("status"),
                "instrument_symbol": summary.get("instrument", {}).get("symbol"),
                "interval": summary.get("interval"),
                "total_return_pct": total_return,
                "max_drawdown_pct": max_drawdown,
                "sharpe_ratio": sharpe,
                "total_trades": trades,
                "total_net_pnl": strategy.get("total_net_pnl"),
            }
        )
    cards = (
        {
            "label": "Total Return %",
            "direction": "higher_is_better",
            **_numeric(ret_values, "max"),
        },
        {
            "label": "Max Drawdown %",
            "direction": "lower_is_better",
            **_numeric(dd_values, "min"),
        },
        {
            "label": "Sharpe Ratio",
            "direction": "higher_is_better",
            **_numeric(sharpe_values, "max"),
        },
        {
            "label": "Total Trades",
            "direction": "higher_is_better",
            **_numeric(trades_values, "max"),
        },
    )
    return CompareRunsResult(mode="strategy", warnings=(), cards=cards, rows=tuple(rows))


def _ml_compare(run_ids: list[str], details: list[dict[str, Any]]) -> CompareRunsResult:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    validation_values: list[tuple[str, float | None]] = []
    test_values: list[tuple[str, float | None]] = []
    executed_values: list[tuple[str, float | None]] = []
    task_types = {
        (detail.get("summary", {}).get("ml") or {}).get("task_type")
        for detail in details
    }
    if len(task_types - {None}) > 1:
        raise ValueError("ML compare requires the same task_type across selected runs")
    for run_id, detail in zip(run_ids, details, strict=True):
        summary = detail.get("summary", {})
        ml = summary.get("ml") or {}
        validation_values.append(
            (run_id, None if ml.get("best_validation_value") is None else float(ml.get("best_validation_value")))
        )
        test_values.append(
            (run_id, None if ml.get("best_test_value") is None else float(ml.get("best_test_value")))
        )
        executed_values.append(
            (run_id, None if ml.get("model_count_executed") is None else float(ml.get("model_count_executed")))
        )
        if ml.get("primary_metric_name") is None:
            warnings.append(f"{run_id}:missing_primary_metric_name")
        rows.append(
            {
                "run_id": run_id,
                "run_name": summary.get("run_name"),
                "workflow_type": summary.get("workflow_type"),
                "status": summary.get("status"),
                "instrument_symbol": summary.get("instrument", {}).get("symbol"),
                "interval": summary.get("interval"),
                "task_type": ml.get("task_type"),
                "target_label": ml.get("target_label"),
                "best_model_id": ml.get("best_model_id"),
                "primary_metric_name": ml.get("primary_metric_name"),
                "best_validation_value": ml.get("best_validation_value"),
                "best_test_value": ml.get("best_test_value"),
                "model_count_executed": ml.get("model_count_executed"),
                "model_count_skipped": ml.get("model_count_skipped"),
            }
        )
    cards = (
        {
            "label": "Best Validation",
            "direction": "higher_is_better",
            **_numeric(validation_values, "max"),
        },
        {
            "label": "Best Test",
            "direction": "higher_is_better",
            **_numeric(test_values, "max"),
        },
        {
            "label": "Executed Models",
            "direction": "higher_is_better",
            **_numeric(executed_values, "max"),
        },
    )
    return CompareRunsResult(mode="ml", warnings=tuple(warnings), cards=cards, rows=tuple(rows))


def compare_saved_runs(
    *,
    root_dir: Path,
    run_ids: list[str],
    mode: str = "auto",
) -> CompareRunsResult:
    unique_ids: list[str] = []
    for run_id in run_ids:
        if run_id not in unique_ids:
            unique_ids.append(run_id)
    if len(unique_ids) < 2 or len(unique_ids) > 5:
        raise ValueError("compare requires between 2 and 5 unique run_ids")

    manifests = [get_run_manifest(root_dir, run_id) for run_id in unique_ids]
    details = [get_run_detail(root_dir, run_id) for run_id in unique_ids]
    resolved_mode = _mode_for_details(mode, details)
    missing_rows = [
        manifest["run_id"]
        for manifest, detail in zip(manifests, details, strict=True)
        if detail.get(f"{resolved_mode}_detail") is None
    ]
    if missing_rows:
        raise ValueError(
            f"Selected runs are not compatible for {resolved_mode} compare: {', '.join(missing_rows)}"
        )

    if resolved_mode == "strategy":
        result = _strategy_compare(unique_ids, details)
    else:
        result = _ml_compare(unique_ids, details)
    if any(manifest.get("interval") != manifests[0].get("interval") for manifest in manifests[1:]):
        return CompareRunsResult(
            mode=result.mode,
            warnings=result.warnings + ("interval_mismatch",),
            cards=result.cards,
            rows=result.rows,
        )
    return result
