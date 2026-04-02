"""Local artifact persistence helpers for run history/index management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from .artifacts import ResearchRunArtifact
from .persisted_models import PersistedRunSummary

SCHEMA_VERSION = 1
INDEX_FILENAME = "index.json"
MANIFEST_FILENAME = "manifest.json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temp_path.replace(path)


def _parse_dt(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _iso_or_none(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


@dataclass(frozen=True)
class RunManifest:
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
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["started_at"] = _iso_or_none(self.started_at)
        payload["ended_at"] = _iso_or_none(self.ended_at)
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        return payload

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "RunManifest":
        return RunManifest(
            schema_version=int(payload.get("schema_version", SCHEMA_VERSION)),
            run_id=str(payload["run_id"]),
            run_name=str(payload.get("run_name", payload["run_id"])),
            workflow_type=str(payload.get("workflow_type", "unknown")),
            status=str(payload.get("status", "unknown")),
            started_at=_parse_dt(payload.get("started_at")),
            ended_at=_parse_dt(payload.get("ended_at")),
            duration_ms=(
                None
                if payload.get("duration_ms") is None
                else int(payload.get("duration_ms"))
            ),
            instrument_symbol=str(payload.get("instrument_symbol", "unknown")),
            asset_class=(
                None if payload.get("asset_class") is None else str(payload.get("asset_class"))
            ),
            interval=None if payload.get("interval") is None else str(payload.get("interval")),
            candle_count=(
                None if payload.get("candle_count") is None else int(payload.get("candle_count"))
            ),
            has_strategy=bool(payload.get("has_strategy", False)),
            has_ml=bool(payload.get("has_ml", False)),
            summary_path=str(payload.get("summary_path", "")),
            detail_path=(
                None if payload.get("detail_path") is None else str(payload.get("detail_path"))
            ),
            created_at=_parse_dt(payload.get("created_at")) or _utcnow(),
            updated_at=_parse_dt(payload.get("updated_at")) or _utcnow(),
        )


@dataclass(frozen=True)
class RunIndexRecord:
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
    has_strategy: bool
    has_ml: bool
    summary_available: bool
    detail_available: bool
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_name": self.run_name,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "started_at": _iso_or_none(self.started_at),
            "ended_at": _iso_or_none(self.ended_at),
            "duration_ms": self.duration_ms,
            "instrument_symbol": self.instrument_symbol,
            "asset_class": self.asset_class,
            "interval": self.interval,
            "has_strategy": self.has_strategy,
            "has_ml": self.has_ml,
            "summary_available": self.summary_available,
            "detail_available": self.detail_available,
            "updated_at": self.updated_at.isoformat(),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "RunIndexRecord":
        return RunIndexRecord(
            run_id=str(payload["run_id"]),
            run_name=str(payload.get("run_name", payload["run_id"])),
            workflow_type=str(payload.get("workflow_type", "unknown")),
            status=str(payload.get("status", "unknown")),
            started_at=_parse_dt(payload.get("started_at")),
            ended_at=_parse_dt(payload.get("ended_at")),
            duration_ms=(
                None
                if payload.get("duration_ms") is None
                else int(payload.get("duration_ms"))
            ),
            instrument_symbol=str(payload.get("instrument_symbol", "unknown")),
            asset_class=(
                None if payload.get("asset_class") is None else str(payload.get("asset_class"))
            ),
            interval=None if payload.get("interval") is None else str(payload.get("interval")),
            has_strategy=bool(payload.get("has_strategy", False)),
            has_ml=bool(payload.get("has_ml", False)),
            summary_available=bool(payload.get("summary_available", False)),
            detail_available=bool(payload.get("detail_available", False)),
            updated_at=_parse_dt(payload.get("updated_at")) or _utcnow(),
        )


@dataclass(frozen=True)
class RunIndex:
    schema_version: int
    generated_at: datetime
    runs: tuple[RunIndexRecord, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "runs": [record.to_dict() for record in self.runs],
            "warnings": list(self.warnings),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "RunIndex":
        return RunIndex(
            schema_version=int(payload.get("schema_version", SCHEMA_VERSION)),
            generated_at=_parse_dt(payload.get("generated_at")) or _utcnow(),
            runs=tuple(
                RunIndexRecord.from_dict(record)
                for record in payload.get("runs", [])
                if isinstance(record, Mapping)
            ),
            warnings=tuple(str(w) for w in payload.get("warnings", []) if isinstance(w, str)),
        )


def manifest_path_for_run(root_dir: Path, run_id: str) -> Path:
    return root_dir / run_id / MANIFEST_FILENAME


def index_path(root_dir: Path) -> Path:
    return root_dir / INDEX_FILENAME


def build_manifest_from_summary(
    *,
    root_dir: Path,
    run_id: str,
    summary: PersistedRunSummary,
    summary_path: Path,
    detail_path: Path | None,
    existing_manifest: RunManifest | None = None,
) -> RunManifest:
    now = _utcnow()
    return RunManifest(
        schema_version=SCHEMA_VERSION,
        run_id=run_id,
        run_name=summary.run_name,
        workflow_type=summary.workflow_type,
        status=summary.status,
        started_at=summary.started_at,
        ended_at=summary.ended_at,
        duration_ms=summary.duration_ms,
        instrument_symbol=summary.instrument.symbol,
        asset_class=summary.instrument.asset_class,
        interval=summary.interval,
        candle_count=summary.candle_count,
        has_strategy=summary.strategy is not None,
        has_ml=summary.ml is not None,
        summary_path=str(summary_path.relative_to(root_dir).as_posix()),
        detail_path=(
            None
            if detail_path is None or not detail_path.exists()
            else str(detail_path.relative_to(root_dir).as_posix())
        ),
        created_at=(existing_manifest.created_at if existing_manifest else now),
        updated_at=now,
    )


def manifest_to_index_record(manifest: RunManifest, root_dir: Path) -> RunIndexRecord:
    summary_abs = root_dir / manifest.summary_path
    detail_abs = None if manifest.detail_path is None else root_dir / manifest.detail_path
    return RunIndexRecord(
        run_id=manifest.run_id,
        run_name=manifest.run_name,
        workflow_type=manifest.workflow_type,
        status=manifest.status,
        started_at=manifest.started_at,
        ended_at=manifest.ended_at,
        duration_ms=manifest.duration_ms,
        instrument_symbol=manifest.instrument_symbol,
        asset_class=manifest.asset_class,
        interval=manifest.interval,
        has_strategy=manifest.has_strategy,
        has_ml=manifest.has_ml,
        summary_available=summary_abs.exists(),
        detail_available=False if detail_abs is None else detail_abs.exists(),
        updated_at=manifest.updated_at,
    )


def load_manifest(root_dir: Path, run_id: str) -> RunManifest | None:
    path = manifest_path_for_run(root_dir, run_id)
    if not path.exists():
        return None
    payload = _read_json(path)
    return RunManifest.from_dict(payload)


def write_manifest(root_dir: Path, manifest: RunManifest) -> Path:
    path = manifest_path_for_run(root_dir, manifest.run_id)
    _atomic_write_json(path, manifest.to_dict())
    return path


def load_index(root_dir: Path) -> RunIndex:
    path = index_path(root_dir)
    if not path.exists():
        return rebuild_index(root_dir)
    try:
        payload = _read_json(path)
    except (OSError, ValueError, TypeError):
        rebuilt = rebuild_index(root_dir)
        return RunIndex(
            schema_version=rebuilt.schema_version,
            generated_at=rebuilt.generated_at,
            runs=rebuilt.runs,
            warnings=tuple(rebuilt.warnings) + ("index_corrupt_rebuilt",),
        )
    return RunIndex.from_dict(payload)


def write_index(root_dir: Path, index: RunIndex) -> Path:
    path = index_path(root_dir)
    _atomic_write_json(path, index.to_dict())
    return path


def rebuild_index(root_dir: Path) -> RunIndex:
    root_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    manifests: list[RunManifest] = []
    for summary_file in sorted(root_dir.glob("*/summary.json")):
        run_dir = summary_file.parent
        run_id = run_dir.name
        detail_file = run_dir / "detail.json"
        manifest_file = run_dir / MANIFEST_FILENAME
        try:
            summary = PersistedRunSummary.load(summary_file)
        except (OSError, ValueError, TypeError):
            warnings.append(f"{run_id}:invalid_summary_json")
            continue
        existing_manifest = None
        if manifest_file.exists():
            try:
                existing_manifest = RunManifest.from_dict(_read_json(manifest_file))
            except (OSError, ValueError, TypeError):
                warnings.append(f"{run_id}:invalid_manifest_json")
        manifest = build_manifest_from_summary(
            root_dir=root_dir,
            run_id=run_id,
            summary=summary,
            summary_path=summary_file,
            detail_path=detail_file if detail_file.exists() else None,
            existing_manifest=existing_manifest,
        )
        write_manifest(root_dir, manifest)
        manifests.append(manifest)
    records = sorted(
        (manifest_to_index_record(manifest, root_dir) for manifest in manifests),
        key=lambda record: record.started_at or record.updated_at,
        reverse=True,
    )
    index = RunIndex(
        schema_version=SCHEMA_VERSION,
        generated_at=_utcnow(),
        runs=tuple(records),
        warnings=tuple(warnings),
    )
    write_index(root_dir, index)
    return index


def upsert_run_index_entry(
    *,
    root_dir: Path,
    manifest: RunManifest,
) -> RunIndex:
    current = load_index(root_dir)
    by_id: dict[str, RunIndexRecord] = {record.run_id: record for record in current.runs}
    by_id[manifest.run_id] = manifest_to_index_record(manifest, root_dir)
    runs = sorted(
        by_id.values(),
        key=lambda record: record.started_at or record.updated_at,
        reverse=True,
    )
    updated = RunIndex(
        schema_version=SCHEMA_VERSION,
        generated_at=_utcnow(),
        runs=tuple(runs),
        warnings=current.warnings,
    )
    write_index(root_dir, updated)
    return updated


def persist_run_with_index(
    *,
    root_dir: Path,
    artifact: ResearchRunArtifact,
    summary_path: Path,
    detail_path: Path,
) -> tuple[RunManifest, RunIndex]:
    summary = artifact.to_persisted_summary()
    existing_manifest = load_manifest(root_dir, artifact.run_id)
    manifest = build_manifest_from_summary(
        root_dir=root_dir,
        run_id=artifact.run_id,
        summary=summary,
        summary_path=summary_path,
        detail_path=detail_path,
        existing_manifest=existing_manifest,
    )
    write_manifest(root_dir, manifest)
    updated_index = upsert_run_index_entry(root_dir=root_dir, manifest=manifest)
    return manifest, updated_index
