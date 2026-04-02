"""Helpers for hydrating and reconciling DB metadata from research artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .research_runs import (
    METADATA_SOURCE_ARTIFACT_RECONCILED,
    METADATA_SOURCE_LEGACY_BACKFILL,
    ResearchRunMetadataQuery,
    ResearchRunMetadataRecord,
    ResearchRunMetadataRepository,
    build_run_metadata_record,
)


@dataclass(frozen=True)
class MetadataTransitionReport:
    artifact_runs: int
    db_rows: int
    db_backed_runs: int
    legacy_only_runs: int
    drifted_runs: int
    malformed_runs: int
    orphaned_db_rows: int
    warnings: tuple[str, ...]

    @property
    def backfill_complete(self) -> bool:
        return (
            self.legacy_only_runs == 0
            and self.drifted_runs == 0
            and self.malformed_runs == 0
        )


@dataclass(frozen=True)
class BackfillResult:
    inserted_count: int
    updated_count: int
    unchanged_count: int
    skipped_count: int
    orphaned_db_row_count: int
    warnings: tuple[str, ...]
    report: MetadataTransitionReport

    @property
    def imported_count(self) -> int:
        return self.inserted_count + self.updated_count


def _load_artifact_metadata_record(
    *,
    root_dir: Path,
    run_id: str,
    metadata_source: str,
) -> ResearchRunMetadataRecord:
    from research.history import load_saved_run_bundle

    bundle = load_saved_run_bundle(root_dir, run_id)
    return build_run_metadata_record(
        root_dir=root_dir,
        summary=bundle.summary,
        manifest=bundle.manifest,
        metadata_source=metadata_source,
    )


def _artifact_run_ids(root_dir: Path) -> tuple[str, ...]:
    return tuple(summary_path.parent.name for summary_path in sorted(root_dir.glob("*/summary.json")))


def _scan_artifact_metadata_records(
    *,
    root_dir: Path,
    metadata_source: str,
) -> tuple[dict[str, ResearchRunMetadataRecord], tuple[str, ...], int]:
    records: dict[str, ResearchRunMetadataRecord] = {}
    warnings: list[str] = []
    malformed_runs = 0
    for run_id in _artifact_run_ids(root_dir):
        try:
            records[run_id] = _load_artifact_metadata_record(
                root_dir=root_dir,
                run_id=run_id,
                metadata_source=metadata_source,
            )
        except (OSError, TypeError, ValueError, FileNotFoundError, KeyError) as exc:
            malformed_runs += 1
            warnings.append(f"{run_id}:skip_backfill:{type(exc).__name__}")
    return records, tuple(warnings), malformed_runs


def _load_db_rows(
    repository: ResearchRunMetadataRepository,
) -> dict[str, ResearchRunMetadataRecord]:
    result = repository.list_run_metadata(
        ResearchRunMetadataQuery(limit=None, offset=0, sort="started_desc")
    )
    return {item.run_id: item for item in result.items}


def report_research_run_metadata_transition(
    *,
    root_dir: Path,
    repository: ResearchRunMetadataRepository,
) -> MetadataTransitionReport:
    db_rows = _load_db_rows(repository)
    artifact_records, warnings, malformed_runs = _scan_artifact_metadata_records(
        root_dir=root_dir,
        metadata_source=METADATA_SOURCE_LEGACY_BACKFILL,
    )
    artifact_run_ids = set(_artifact_run_ids(root_dir))
    db_ids = set(db_rows)
    artifact_ids = set(artifact_records)
    shared_ids = artifact_ids & db_ids
    drifted_runs = sum(
        1
        for run_id in shared_ids
        if db_rows[run_id].artifact_fingerprint != artifact_records[run_id].artifact_fingerprint
    )
    return MetadataTransitionReport(
        artifact_runs=len(artifact_run_ids),
        db_rows=len(db_rows),
        db_backed_runs=len(shared_ids),
        legacy_only_runs=len(artifact_ids - db_ids),
        drifted_runs=drifted_runs,
        malformed_runs=malformed_runs,
        orphaned_db_rows=len(db_ids - artifact_run_ids),
        warnings=warnings,
    )


def backfill_research_run_metadata(
    *,
    root_dir: Path,
    repository: ResearchRunMetadataRepository,
) -> BackfillResult:
    db_rows = _load_db_rows(repository)
    artifact_records, warnings, _ = _scan_artifact_metadata_records(
        root_dir=root_dir,
        metadata_source=METADATA_SOURCE_LEGACY_BACKFILL,
    )

    inserted = 0
    updated = 0
    unchanged = 0
    for run_id, legacy_record in artifact_records.items():
        existing = db_rows.get(run_id)
        if existing is None:
            repository.upsert_run_metadata(legacy_record)
            inserted += 1
            continue
        if existing.artifact_fingerprint == legacy_record.artifact_fingerprint:
            unchanged += 1
            continue
        repository.upsert_run_metadata(
            _load_artifact_metadata_record(
                root_dir=root_dir,
                run_id=run_id,
                metadata_source=METADATA_SOURCE_ARTIFACT_RECONCILED,
            )
        )
        updated += 1

    report = report_research_run_metadata_transition(
        root_dir=root_dir,
        repository=repository,
    )
    return BackfillResult(
        inserted_count=inserted,
        updated_count=updated,
        unchanged_count=unchanged,
        skipped_count=report.malformed_runs,
        orphaned_db_row_count=report.orphaned_db_rows,
        warnings=tuple(warnings),
        report=report,
    )
