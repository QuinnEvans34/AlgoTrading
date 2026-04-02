"""Backfill DB metadata rows from existing research artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from _common import DEFAULT_ENV_FILE, ROOT, load_env_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill research metadata into the database")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env file path (default: .env)",
    )
    parser.add_argument(
        "--root-dir",
        default=None,
        help="Optional research artifact root override",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print migration/backfill completeness without modifying DB rows",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))

    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))

    from config import AppSettings
    from persistence import (
        SQLAlchemyResearchRunMetadataRepository,
        backfill_research_run_metadata,
        create_database_manager,
        report_research_run_metadata_transition,
    )

    app_settings = AppSettings.from_env()
    manager = create_database_manager(app_settings.database)
    if manager is None:
        print("Database metadata persistence is disabled. Set DATABASE_ENABLED and DATABASE_URL first.")
        return 2

    root_dir = (
        Path(args.root_dir)
        if args.root_dir is not None
        else ROOT / app_settings.storage.run_output_dir
    )
    repository = SQLAlchemyResearchRunMetadataRepository(
        session_factory=manager.session_factory
    )
    if args.report_only:
        report = report_research_run_metadata_transition(
            root_dir=root_dir,
            repository=repository,
        )
        print(f"Artifact runs: {report.artifact_runs}")
        print(f"DB rows: {report.db_rows}")
        print(f"DB-backed runs: {report.db_backed_runs}")
        print(f"Legacy-only runs: {report.legacy_only_runs}")
        print(f"Drifted runs: {report.drifted_runs}")
        print(f"Malformed runs: {report.malformed_runs}")
        print(f"Orphaned DB rows: {report.orphaned_db_rows}")
        print(f"Backfill complete: {'yes' if report.backfill_complete else 'no'}")
        if report.warnings:
            print("Warnings:")
            for warning in report.warnings:
                print(f"  - {warning}")
        return 0

    result = backfill_research_run_metadata(root_dir=root_dir, repository=repository)
    print(f"Inserted: {result.inserted_count}")
    print(f"Updated: {result.updated_count}")
    print(f"Unchanged: {result.unchanged_count}")
    print(f"Skipped: {result.skipped_count}")
    print(f"Orphaned DB rows: {result.orphaned_db_row_count}")
    print(f"Backfill complete: {'yes' if result.report.backfill_complete else 'no'}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
