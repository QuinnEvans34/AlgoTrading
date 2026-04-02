"""Run history listing and artifact retrieval services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

from persistence.errors import PersistenceUnavailableError
from persistence.research_runs import (
    ResearchRunMetadataQuery,
    ResearchRunMetadataRecord,
    ResearchRunMetadataRepository,
)
from .persisted_models import (
    LoadedSavedRunBundle,
    PersistedManifestView,
    PersistedRunDetail,
    PersistedRunSummary,
)
from .storage import (
    RunIndexRecord,
    RunManifest,
    index_path,
    load_index,
    rebuild_index,
)

LOGGER = logging.getLogger(__name__)


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


def _validate_run_id(run_id: str) -> None:
    if run_id.strip() == "" or "/" in run_id or "\\" in run_id:
        raise ValueError("run_id must be a non-empty path-safe identifier")


def _normalize_index(root_dir: Path):
    idx_path = index_path(root_dir)
    if not idx_path.exists():
        return rebuild_index(root_dir)
    return load_index(root_dir)


def _summary_path(root_dir: Path, run_id: str) -> Path:
    return root_dir / run_id / "summary.json"


def _detail_path(root_dir: Path, run_id: str) -> Path:
    return root_dir / run_id / "detail.json"


def _artifact_path(
    root_dir: Path,
    run_id: str,
    *,
    relative_path: str | None,
    default_name: str,
) -> Path:
    if relative_path:
        candidate = root_dir / Path(relative_path)
        if candidate.exists():
            return candidate
    return root_dir / run_id / default_name


def _manifest_view_from_loaded_manifest(manifest, *, synthetic: bool) -> PersistedManifestView:  # noqa: ANN001
    return PersistedManifestView(
        schema_version=manifest.schema_version,
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
        candle_count=manifest.candle_count,
        has_strategy=manifest.has_strategy,
        has_ml=manifest.has_ml,
        summary_path=manifest.summary_path,
        detail_path=manifest.detail_path,
        created_at=manifest.created_at,
        updated_at=manifest.updated_at,
        synthetic=synthetic,
    )


def _index_record_from_metadata(
    record: ResearchRunMetadataRecord,
) -> RunIndexRecord:
    return RunIndexRecord(
        run_id=record.run_id,
        run_name=record.run_name,
        workflow_type=record.workflow_type,
        status=record.status,
        started_at=record.started_at,
        ended_at=record.ended_at,
        duration_ms=record.duration_ms,
        instrument_symbol=record.instrument_symbol,
        asset_class=record.asset_class,
        interval=record.interval,
        has_strategy=record.has_strategy,
        has_ml=record.has_ml,
        summary_available=record.summary_available,
        detail_available=record.detail_available,
        updated_at=record.updated_at,
    )


def _index_record_from_summary_and_manifest(
    *,
    root_dir: Path,
    summary: PersistedRunSummary,
    manifest: PersistedManifestView,
) -> RunIndexRecord:
    detail_available = False
    if manifest.detail_path is not None:
        detail_available = (root_dir / manifest.detail_path).exists()
    updated_at = manifest.updated_at or summary.ended_at
    return RunIndexRecord(
        run_id=summary.run_id,
        run_name=summary.run_name,
        workflow_type=summary.workflow_type,
        status=summary.status,
        started_at=summary.started_at,
        ended_at=summary.ended_at,
        duration_ms=summary.duration_ms,
        instrument_symbol=summary.instrument.symbol,
        asset_class=summary.instrument.asset_class,
        interval=summary.interval,
        has_strategy=summary.strategy is not None,
        has_ml=summary.ml is not None,
        summary_available=True,
        detail_available=detail_available,
        updated_at=updated_at,
    )


def _synthesize_manifest(
    *,
    root_dir: Path,
    run_id: str,
    summary: PersistedRunSummary,
) -> PersistedManifestView:
    detail_file = _detail_path(root_dir, run_id)
    return PersistedManifestView(
        schema_version=0,
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
        summary_path=f"{run_id}/summary.json",
        detail_path=f"{run_id}/detail.json" if detail_file.exists() else None,
        synthetic=True,
    )


def _load_manifest_from_artifact_path(path: Path) -> RunManifest | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a JSON object")
    return RunManifest.from_dict(payload)


def load_persisted_run_summary(
    root_dir: Path,
    run_id: str,
    metadata: ResearchRunMetadataRecord | None = None,
) -> PersistedRunSummary:
    _validate_run_id(run_id)
    summary_path = _artifact_path(
        root_dir,
        run_id,
        relative_path=None if metadata is None else metadata.summary_path,
        default_name="summary.json",
    )
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary not found for run_id '{run_id}'")
    return PersistedRunSummary.load(summary_path)


def load_persisted_run_detail(
    root_dir: Path,
    run_id: str,
    metadata: ResearchRunMetadataRecord | None = None,
) -> PersistedRunDetail:
    summary = load_persisted_run_summary(root_dir, run_id, metadata=metadata)
    return _load_persisted_run_detail_with_summary(
        root_dir,
        run_id,
        summary,
        metadata=metadata,
    )


def _load_persisted_run_detail_with_summary(
    root_dir: Path,
    run_id: str,
    summary: PersistedRunSummary,
    *,
    metadata: ResearchRunMetadataRecord | None = None,
) -> PersistedRunDetail:
    detail_path = _artifact_path(
        root_dir,
        run_id,
        relative_path=None if metadata is None else metadata.detail_path,
        default_name="detail.json",
    )
    if not detail_path.exists():
        return PersistedRunDetail.summary_only(summary)
    try:
        import json

        payload = json.loads(detail_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("detail payload must be a JSON object")
        return PersistedRunDetail.from_dict(payload, summary=summary)
    except (OSError, ValueError, TypeError):
        return PersistedRunDetail.summary_only(summary)


def load_persisted_run_manifest(
    root_dir: Path,
    run_id: str,
    metadata: ResearchRunMetadataRecord | None = None,
) -> PersistedManifestView:
    summary = load_persisted_run_summary(root_dir, run_id, metadata=metadata)
    return _load_persisted_run_manifest_with_summary(
        root_dir,
        run_id,
        summary,
        metadata=metadata,
    )


def _load_persisted_run_manifest_with_summary(
    root_dir: Path,
    run_id: str,
    summary: PersistedRunSummary,
    *,
    metadata: ResearchRunMetadataRecord | None = None,
) -> PersistedManifestView:
    try:
        manifest = _load_manifest_from_artifact_path(
            _artifact_path(
                root_dir,
                run_id,
                relative_path=None if metadata is None else metadata.manifest_path,
                default_name="manifest.json",
            )
        )
    except (OSError, ValueError, TypeError, KeyError):
        manifest = None
    if manifest is None:
        return _synthesize_manifest(root_dir=root_dir, run_id=run_id, summary=summary)
    return _manifest_view_from_loaded_manifest(manifest, synthetic=False)


def load_saved_run_bundle(
    root_dir: Path,
    run_id: str,
    metadata: ResearchRunMetadataRecord | None = None,
) -> LoadedSavedRunBundle:
    summary = load_persisted_run_summary(root_dir, run_id, metadata=metadata)
    return LoadedSavedRunBundle(
        summary=summary,
        detail=_load_persisted_run_detail_with_summary(
            root_dir,
            run_id,
            summary,
            metadata=metadata,
        ),
        manifest=_load_persisted_run_manifest_with_summary(
            root_dir,
            run_id,
            summary,
            metadata=metadata,
        ),
    )


def _db_query_for_history(query: RunHistoryQuery) -> ResearchRunMetadataQuery:
    return ResearchRunMetadataQuery(
        workflow_type=query.workflow_type,
        status=query.status,
        search=query.search,
        started_after=query.started_after,
        started_before=query.started_before,
        sort=query.sort,
        limit=None,
        offset=0,
    )


def _history_sort_key(record: RunIndexRecord) -> tuple[datetime, str]:
    return (_normalized_sort_datetime(record.started_at or record.updated_at), record.run_id)


def _normalized_sort_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _sort_history_records(records: list[RunIndexRecord], sort: str) -> None:
    if sort == "started_asc":
        records.sort(key=_history_sort_key)
        return
    records.sort(key=_history_sort_key, reverse=True)


def _record_matches_query(record: RunIndexRecord, query: RunHistoryQuery) -> bool:
    if query.workflow_type and record.workflow_type != query.workflow_type:
        return False
    if query.status and record.status != query.status:
        return False
    if query.search:
        needle = query.search.lower()
        if (
            needle not in record.run_id.lower()
            and needle not in record.run_name.lower()
            and needle not in record.instrument_symbol.lower()
        ):
            return False
    if query.started_after and (
        record.started_at is None or record.started_at < query.started_after
    ):
        return False
    if query.started_before and (
        record.started_at is None or record.started_at > query.started_before
    ):
        return False
    return True


def _list_run_history_from_files(root_dir: Path, query: RunHistoryQuery) -> tuple[list[RunIndexRecord], tuple[str, ...]]:
    index = _normalize_index(root_dir)
    records = list(index.runs)
    records = [record for record in records if _record_matches_query(record, query)]
    _sort_history_records(records, query.sort)
    return records, index.warnings


def _list_legacy_run_history_from_artifacts(
    root_dir: Path,
    query: RunHistoryQuery,
    *,
    excluded_run_ids: set[str],
) -> tuple[list[RunIndexRecord], tuple[str, ...]]:
    records: list[RunIndexRecord] = []
    warnings: list[str] = []
    for summary_path in sorted(root_dir.glob("*/summary.json")):
        run_id = summary_path.parent.name
        if run_id in excluded_run_ids:
            continue
        try:
            summary = PersistedRunSummary.load(summary_path)
            manifest = _load_persisted_run_manifest_with_summary(
                root_dir,
                run_id,
                summary,
                metadata=None,
            )
            record = _index_record_from_summary_and_manifest(
                root_dir=root_dir,
                summary=summary,
                manifest=manifest,
            )
        except (OSError, ValueError, TypeError, KeyError) as exc:
            warnings.append(f"{run_id}:legacy_metadata_skip:{type(exc).__name__}")
            continue
        if _record_matches_query(record, query):
            records.append(record)
    _sort_history_records(records, query.sort)
    return records, tuple(warnings)


def _page_records(records: list[RunIndexRecord], query: RunHistoryQuery) -> RunHistoryListResult:
    total = len(records)
    start = max(0, query.offset)
    end = max(start, start + max(1, query.limit))
    page = records[start:end]
    return RunHistoryListResult(
        items=tuple(page),
        total=total,
        limit=query.limit,
        offset=query.offset,
        warnings=(),
    )


def list_run_history(
    root_dir: Path,
    query: RunHistoryQuery,
    metadata_repository: ResearchRunMetadataRepository | None = None,
) -> RunHistoryListResult:
    if metadata_repository is None:
        file_records, file_warnings = _list_run_history_from_files(root_dir, query)
        return RunHistoryListResult(
            items=tuple(_page_records(file_records, query).items),
            total=len(file_records),
            limit=query.limit,
            offset=query.offset,
            warnings=tuple(file_warnings),
        )
    try:
        known_run_ids = metadata_repository.list_known_run_ids()
        db_result = metadata_repository.list_run_metadata(_db_query_for_history(query))
    except PersistenceUnavailableError as exc:
        file_records, file_warnings = _list_run_history_from_files(root_dir, query)
        warnings = list(file_warnings)
        LOGGER.warning(
            "Research metadata DB unavailable during history listing; falling back to file index. %s",
            exc,
        )
        warnings.append("db_metadata_unavailable_fallback")
        return RunHistoryListResult(
            items=tuple(_page_records(file_records, query).items),
            total=len(file_records),
            limit=query.limit,
            offset=query.offset,
            warnings=tuple(warnings),
        )

    db_records = [_index_record_from_metadata(item) for item in db_result.items]
    legacy_records, legacy_warnings = _list_legacy_run_history_from_artifacts(
        root_dir,
        query,
        excluded_run_ids=known_run_ids,
    )
    merged_records = [*db_records, *legacy_records]
    _sort_history_records(merged_records, query.sort)
    paged = _page_records(merged_records, query)
    return RunHistoryListResult(
        items=paged.items,
        total=paged.total,
        limit=paged.limit,
        offset=paged.offset,
        warnings=legacy_warnings,
    )


def get_run_summary(root_dir: Path, run_id: str) -> dict[str, Any]:
    return load_persisted_run_summary(root_dir, run_id).to_dict()


def get_run_detail(root_dir: Path, run_id: str) -> dict[str, Any]:
    return load_persisted_run_detail(root_dir, run_id).to_dict()


def get_run_manifest(root_dir: Path, run_id: str) -> dict[str, Any]:
    return load_persisted_run_manifest(root_dir, run_id).to_dict()
