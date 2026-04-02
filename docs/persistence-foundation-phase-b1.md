# Persistence Foundation Phase B1

## Before B1
- Research persistence was file-first only.
- New runs wrote `summary.json`, `detail.json`, `manifest.json`, and root `index.json` under `artifacts/research_runs`.
- History listing depended on `index.json` plus rebuild logic from per-run artifacts.
- Detail and compare reopened runs from saved artifacts on disk.
- There was no database-backed source for saved-run discovery metadata.

## Technology Choice
- Database: PostgreSQL
- Python stack: SQLAlchemy 2.x, psycopg 3, Alembic

Why:
- This matches the intended production direction for the project.
- SQLAlchemy + Alembic gives a conservative migration path without forcing a larger ORM-heavy redesign.
- Sync access fits the current backend architecture and avoids rewriting route/service wiring.

## Schema Introduced
- Table: `research_run_metadata`

Stored fields are limited to metadata useful for discovery, listing, filtering, and compare selection:
- run identity: `run_id`, `run_name`, `workflow_type`, `status`
- timing: `started_at`, `ended_at`, `duration_ms`
- instrument context: `instrument_symbol`, `asset_class`, `interval`, `candle_count`, `candle_source_type`
- branch flags: `has_strategy`, `has_ml`
- strategy summary fields: `strategy_id`, `total_trades`, `total_return_pct`, `total_net_pnl`, `max_drawdown_pct`, `sharpe_ratio`
- ML summary fields: `ml_task_type`, `ml_target_label`, `ml_best_model_id`, `ml_primary_metric_name`, `ml_best_validation_value`, `ml_best_test_value`, `ml_model_count_executed`, `ml_model_count_skipped`, `ml_warning_count`
- artifact pointers: `summary_path`, `detail_path`, `manifest_path`
- compatibility markers: `metadata_schema_version`, `artifact_schema_version`, `metadata_source`, `manifest_synthetic`
- availability flags: `summary_available`, `detail_available`
- row timestamps: `created_at`, `updated_at`

Indexes added:
- `started_at`
- `(workflow_type, started_at)`
- `(status, started_at)`
- `instrument_symbol`

## Migration Strategy
- Alembic was added with an initial migration: `alembic/versions/0001_research_run_metadata.py`.
- `scripts/dev.py bootstrap` now starts local Postgres through `docker compose`, waits for readiness, and runs `alembic upgrade head` when DB persistence is enabled.
- `DATABASE_ENABLED=false` keeps local development in file-only mode.

## Transition Rule
- B1 uses explicit dual-write for new research runs.
- New runs still write all artifact files exactly as before.
- New runs also upsert a metadata row into `research_run_metadata`.
- Canonical rule:
  - if DB metadata exists for a run, DB metadata wins for listing/discovery
  - if a run is missing from DB, legacy file metadata remains the fallback
  - if DB is enabled but unavailable, history/read flows fall back to file metadata and keep working

This keeps the transition explicit without removing compatibility for older runs.

## How New Runs Persist
1. The research runner writes `summary.json`
2. The research runner writes `detail.json`
3. Manifest and index persistence continues as before
4. The persisted summary + manifest are normalized into a typed `ResearchRunMetadataRecord`
5. That record is upserted through the SQLAlchemy-backed repository

DB write failure is non-fatal after artifact persistence succeeds. The run still completes and remains reopenable from disk.

## Compatibility Strategy For Old Runs
- Existing saved artifacts remain supported without migration.
- History listing now queries DB metadata first, then merges in legacy file/index results for run IDs not present in DB.
- Detail and compare still read `summary.json` and `detail.json` artifacts.
- Manifest-like metadata can be reconstructed from DB rows when available, but file-backed artifacts remain the authoritative source for detailed reopen flows.
- A backfill utility was added for legacy artifacts:
  - `py -3 scripts/backfill_research_metadata.py`

The backfill is explicit and idempotent. It is not run automatically on startup.

## What Remains File-Backed After B1
- `detail.json` and large detail payloads
- per-run `summary.json`
- per-run `manifest.json`
- root `index.json`
- paper trading persistence
- live execution attempt logs and state

B1 establishes the metadata foundation only. It does not migrate full research payloads, paper trading, or live execution into the database.

## Local Developer Setup
1. Copy `.env.example` to `.env`
2. Ensure Docker is running
3. Run:
```bash
py -3 scripts/dev.py bootstrap
```
4. Optional legacy metadata import:
```bash
py -3 scripts/backfill_research_metadata.py
```
5. Start services:
```bash
py -3 scripts/dev.py backend
py -3 scripts/dev.py frontend
```

Relevant env vars:
- `DATABASE_ENABLED`
- `DATABASE_URL`
- `DATABASE_ECHO`

Repo-local Postgres defaults are defined in `docker-compose.yml`.

## How B1 Fits The Existing Structure
- DB wiring and repository logic live under `src/persistence/`
- A.1 API service split remains intact
- A.2 artifact normalization remains the basis for summary/detail/compare reads
- research/history/compare now consume DB metadata conservatively without replacing artifact-backed detail reads

## Tests Added Or Updated
- repository round-trip, filtering, paging, and missing-row tests
- migration bootstrap test
- explicit backfill test
- research runner dual-write test
- DB write failure fallback test
- history DB-preferred listing test
- detail compatibility test with DB metadata + file-backed detail
- compare compatibility tests with DB metadata + artifact-backed compare inputs
- `scripts/dev.py bootstrap` DB path coverage

## Risks And Temporary Compromises
- B1 intentionally leaves two metadata paths alive during transition: DB metadata for new runs and file metadata fallback for legacy runs.
- Detail payloads still live on disk, so compare/detail still depend on artifact availability.
- SQLite is used in tests only for fast repository and integration coverage. Runtime support is Postgres-first.
- `index.json` is still maintained for compatibility even though saved-run discovery is no longer purely index-driven when DB metadata is present.

## Recommended Follow-Up
- Phase B2 should add a first-class metadata backfill/admin workflow and operational observability around DB availability.
- After DB adoption stabilizes, the project can reduce reliance on `index.json` for discovery while keeping artifact files for detailed reopen and auditability.
