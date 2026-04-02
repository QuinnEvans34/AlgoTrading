# Persistence Transition Hardening Phase B2

## What B1 Left Transitional
- B1 established dual-write and DB metadata storage, but history listing still mixed DB rows with `index.json`-driven file records.
- Per-run reads could still treat DB metadata as a manifest-equivalent payload, which left room for drift between DB metadata and artifact-backed reopen content.
- Legacy backfill was safe enough for initial import, but it did not classify `insert/update/unchanged`, detect drift, or report migration completeness clearly.

## Final Source-Of-Truth Policy After B2
- DB metadata is the source of truth for research run history/discovery when the database is configured and reachable.
- Artifact files remain the source of truth for reopen/detail/compare content:
  - `summary.json`
  - `detail.json`
  - `manifest.json` or A.2 synthetic-manifest fallback
- `index.json` is no longer part of the authoritative mixed-source history path when DB metadata is healthy. It remains only for degraded DB-unavailable fallback and legacy compatibility utilities.

## How DB-Primary Behavior Now Works
- History listing now uses a two-source flow:
  1. query DB metadata for all matching DB-backed runs
  2. scan artifact-backed legacy runs for run IDs that are not present in DB
  3. normalize both sources into the same history-record shape
  4. sort once with a stable key: effective timestamp + `run_id`
  5. page after the final merged sort
- This removes the old implicit DB+index merge and prevents duplicate rows for mixed DB/legacy run sets.
- When the DB is unavailable, history falls back explicitly to the legacy index/artifact path and emits `db_metadata_unavailable_fallback`.

## Legacy Fallback Rules
- DB reachable + DB row exists:
  - use DB metadata for history/discovery
  - still load artifacts for summary/detail/compare content
- DB reachable + no DB row:
  - allow legacy artifact-derived metadata as a temporary supplement in history
- DB unavailable:
  - use the legacy file/index fallback path
- Malformed legacy summary artifacts are skipped during DB-primary supplement scanning and reported in warnings.
- Missing or malformed manifests continue to use the Phase A.2 synthetic-manifest behavior.

## Backfill / Import Hardening
- `scripts/backfill_research_metadata.py` now supports:
  - apply mode: import/reconcile metadata rows safely
  - `--report-only`: show migration completeness without modifying DB rows
- Backfill now classifies runs as:
  - inserted
  - updated
  - unchanged
  - skipped
  - orphaned DB row
- Rerunning backfill is idempotent:
  - unchanged rows are reported but not rewritten
  - drifted rows are reconciled from artifacts into DB
  - malformed runs are skipped without corrupting existing DB rows
  - partial imports can be retried safely

## Duplicate And Drift Handling
- Duplicate mixed-source history rows are prevented by excluding DB-known run IDs from the legacy supplement scan.
- Drift is detected by comparing DB rows against an `artifact_fingerprint` computed from the normalized artifact-driven metadata view.
- Reconciliation policy is one-way:
  - artifacts can repair DB metadata
  - DB metadata never rewrites saved artifact files in B2
- If a DB row has no corresponding artifact summary on disk, it is reported as an orphaned DB row.

## Schema Changes Added In B2
- Added to `research_run_metadata`:
  - `artifact_fingerprint`
  - `last_synced_at`
- Metadata source values are now formalized in code:
  - `dual_write`
  - `legacy_backfill`
  - `artifact_reconciled`

## Operational / Developer Workflow
1. Start or bootstrap the local DB:
```bash
py -3 scripts/dev.py bootstrap
```
2. Check transition completeness:
```bash
py -3 scripts/backfill_research_metadata.py --report-only
```
3. Apply import/reconciliation:
```bash
py -3 scripts/backfill_research_metadata.py
```

Practical completeness rule:
- no legacy-only runs
- no drifted runs
- no malformed runs blocking import

## Test Coverage Added
- DB-primary history listing with mixed DB + legacy runs and no duplicates
- deterministic mixed-source ordering via `run_id` tiebreak
- artifact-authoritative history/detail/compare reads when DB metadata drifts
- repeated backfill idempotency
- drift reconciliation from artifacts into DB
- malformed legacy artifact skip behavior
- orphaned DB row reporting
- migration coverage for new transition fields

## Known Remaining Limitations
- `detail.json` and full reopen payloads are still file-backed by design.
- Paper trading and live execution persistence remain outside this transition.
- `index.json` is still written for compatibility, even though it is no longer authoritative when DB metadata is healthy.
- B2 improves visibility through CLI/reporting and docs, not through new public API endpoints.
