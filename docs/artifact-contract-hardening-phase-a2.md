# Artifact Contract Hardening Phase A2

## Current Artifact Shapes Discovered

Persisted research runs currently use:

- per-run `summary.json`
  - top-level fields: `run_id`, `run_name`, `workflow_type`, `status`, `started_at`, `ended_at`, `duration_ms`, `instrument`, `interval`, `candle_count`, `candle_source_type`, `step_results`, `metadata`
  - optional branches: `candle_time_range`, `strategy`, `ml`
- per-run `detail.json`
  - top-level fields: `summary`, `strategy_detail`, `ml_detail`
  - strategy detail includes `backtest_summary`, `performance`, `trade_analysis`, `risk`, `assumptions`, `equity_curve`, `drawdown_curve`, `trades`, `drawdown_episodes`
  - ML detail includes `target_label`, `task_type`, `dataset_metadata`, `comparison_table`, `model_reports`, `run_metadata`, `warnings`
- per-run `manifest.json`
  - typed metadata used for history/index consumption
- root `index.json`
  - typed run listing records plus warnings

Before this phase, only manifest/index were explicitly modeled. Summary/detail reads and compare assembly still depended on flexible nested dict access.

## What Was Normalized

- Added `src/research/persisted_models.py` with typed persisted models for:
  - run summary
  - run detail bundle
  - manifest view used by history/detail reads
  - loaded saved-run bundle
  - compare metric cards and compare rows
- `ResearchRunArtifact` now builds typed persisted summary/detail models first and then dumps them back to the existing JSON shape.
- Storage/index rebuild now derives manifests from typed persisted summaries instead of raw summary dicts.
- History/detail read helpers now normalize disk payloads into typed persisted models before any API mapping.
- Compare assembly now uses normalized summary branch data instead of depending on `detail.json` branch presence for compatibility.

## Compatibility Strategy For Older Artifacts

- No new on-disk schema version was added to `summary.json` or `detail.json` in this phase.
- The current unversioned persisted summary/detail shape is treated as the legacy compatible shape.
- Existing exported helpers `get_run_summary()`, `get_run_detail()`, and `get_run_manifest()` were preserved as dict-returning compatibility wrappers.
- API response contracts were preserved; normalization happens below the API boundary.
- Missing or malformed `manifest.json` is tolerated by synthesizing a manifest from canonical `summary.json`.

## Corruption And Fallback Behavior

- Missing `detail.json` still returns summary-only detail.
- Malformed `detail.json` now also degrades to summary-only detail when `summary.json` is valid.
- Missing `manifest.json` synthesizes a manifest view marked `synthetic=true`.
- Malformed `manifest.json` also synthesizes a manifest view from normalized summary data.
- Missing or corrupt `index.json` still rebuilds from available run directories and preserves warnings.
- Malformed `summary.json` remains a hard failure for that run because it is the canonical source for reopen/history/detail/compare.

## Mapping Into The Post-A.1 API Split

- Research-layer normalization now lives in `src/research/persisted_models.py`, `src/research/history.py`, `src/research/compare.py`, and `src/research/storage.py`.
- The post-A.1 API split remains intact.
- `src/api/_services/history_service.py` now loads normalized saved-run models instead of raw artifact dicts.
- `src/api/serializers.py` now includes adapters from normalized persisted models and typed compare results into existing API schemas.
- `src/api/services.py` remains a thin facade and was not collapsed or expanded in this phase.

## Test Coverage Added

Added or strengthened regression coverage for:

- manifest synthesis when `manifest.json` is missing
- malformed manifest fallback on history read
- malformed detail fallback to summary-only detail
- compare resilience when detail is missing or malformed but summary is valid
- ML compare task-type mismatch rejection
- existing index rebuild fallback coverage remains in place

Validation run:

- focused history/detail/compare backend regressions passed
- full backend unit test suite passed
- existing smoke check passed
- frontend build/typecheck passed

## Known Remaining Fragility

- `summary.json` is still the canonical reopen source; if it is malformed, the run remains unreadable by design.
- Some deep nested detail substructures still carry generic dict payloads for subsystem-native report sections such as `performance`, `risk`, `dataset_metadata`, and `run_metadata`.
- Local-file persistence remains single-user/local-first and is still not intended for concurrent writers or database-like guarantees.
