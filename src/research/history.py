"""Run history listing and artifact retrieval services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .storage import (
    RunIndexRecord,
    index_path,
    load_index,
    load_manifest,
    rebuild_index,
)


@dataclass(frozen=True)
class RunHistoryQuery:
    workflow_type: str | None = None
    status: str | None = None
    search: str | None = None
    started_after: datetime | None = None
    started_before: datetime | None = None
    limit: int = 50
    offset: int = 0
    sort: str = "started_desc"


@dataclass(frozen=True)
class RunHistoryListResult:
    items: tuple[RunIndexRecord, ...]
    total: int
    limit: int
    offset: int
    warnings: tuple[str, ...] = ()


def _read_json(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _validate_run_id(run_id: str) -> None:
    if run_id.strip() == "" or "/" in run_id or "\\" in run_id:
        raise ValueError("run_id must be a non-empty path-safe identifier")


def _build_fallback_detail(summary_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": summary_payload,
        "strategy_detail": None,
        "ml_detail": None,
    }


def _normalize_index(root_dir: Path):
    idx_path = index_path(root_dir)
    if not idx_path.exists():
        return rebuild_index(root_dir)
    return load_index(root_dir)


def list_run_history(root_dir: Path, query: RunHistoryQuery) -> RunHistoryListResult:
    index = _normalize_index(root_dir)
    records = list(index.runs)
    if query.workflow_type:
        records = [record for record in records if record.workflow_type == query.workflow_type]
    if query.status:
        records = [record for record in records if record.status == query.status]
    if query.search:
        needle = query.search.lower()
        records = [
            record
            for record in records
            if needle in record.run_id.lower()
            or needle in record.run_name.lower()
            or needle in record.instrument_symbol.lower()
        ]
    if query.started_after:
        records = [
            record
            for record in records
            if record.started_at is not None and record.started_at >= query.started_after
        ]
    if query.started_before:
        records = [
            record
            for record in records
            if record.started_at is not None and record.started_at <= query.started_before
        ]

    if query.sort == "started_asc":
        records.sort(key=lambda record: record.started_at or record.updated_at)
    else:
        records.sort(key=lambda record: record.started_at or record.updated_at, reverse=True)

    total = len(records)
    start = max(0, query.offset)
    end = max(start, start + max(1, query.limit))
    page = records[start:end]
    return RunHistoryListResult(
        items=tuple(page),
        total=total,
        limit=query.limit,
        offset=query.offset,
        warnings=index.warnings,
    )


def get_run_summary(root_dir: Path, run_id: str) -> dict[str, Any]:
    _validate_run_id(run_id)
    summary_path = root_dir / run_id / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary not found for run_id '{run_id}'")
    return _read_json(summary_path)


def get_run_detail(root_dir: Path, run_id: str) -> dict[str, Any]:
    _validate_run_id(run_id)
    detail_path = root_dir / run_id / "detail.json"
    if detail_path.exists():
        return _read_json(detail_path)
    summary_payload = get_run_summary(root_dir, run_id)
    return _build_fallback_detail(summary_payload)


def get_run_manifest(root_dir: Path, run_id: str) -> dict[str, Any]:
    _validate_run_id(run_id)
    manifest = load_manifest(root_dir, run_id)
    if manifest is None:
        summary = get_run_summary(root_dir, run_id)
        detail_exists = (root_dir / run_id / "detail.json").exists()
        return {
            "run_id": run_id,
            "run_name": summary.get("run_name", run_id),
            "workflow_type": summary.get("workflow_type", "unknown"),
            "status": summary.get("status", "unknown"),
            "started_at": summary.get("started_at"),
            "ended_at": summary.get("ended_at"),
            "duration_ms": summary.get("duration_ms"),
            "instrument_symbol": summary.get("instrument", {}).get("symbol", "unknown"),
            "asset_class": summary.get("instrument", {}).get("asset_class"),
            "interval": summary.get("interval"),
            "candle_count": summary.get("candle_count"),
            "has_strategy": summary.get("strategy") is not None,
            "has_ml": summary.get("ml") is not None,
            "summary_path": f"{run_id}/summary.json",
            "detail_path": f"{run_id}/detail.json" if detail_exists else None,
            "schema_version": 0,
            "synthetic": True,
        }
    payload = manifest.to_dict()
    payload["synthetic"] = False
    return payload
