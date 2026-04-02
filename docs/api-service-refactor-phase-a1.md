# API Service Refactor Phase A1

## Old Structure

Before this refactor, `src/api/services.py` was a single large integration file responsible for:

- health and metadata capability responses
- safe runtime settings projection
- market-data preview request handling
- research run submission and schema-to-domain mapping
- saved run summary/detail reads
- history listing and compare orchestration
- paper trading commands and account reset defaults
- live execution status, readiness, validation, guarded manual submit, and attempt listing

This made `src/api/services.py` the main backend API coupling hotspot even though the underlying domain packages were already separated by concern.

## What Changed

- Added internal collaborator modules under `src/api/_services/`.
- Kept `src/api/services.py` as the stable public facade and compatibility shim.
- Moved domain-specific orchestration into concern-specific modules without changing routes, schemas, dependency wiring, feature flags, error codes, or filesystem persistence behavior.
- Kept route handlers thin and left `api.dependencies.get_api_service()` unchanged.

## Final Module Map

- `src/api/services.py`
  - Thin public `APIService` facade that preserves the existing constructor and public method names.
- `src/api/_services/common.py`
  - Shared helpers for feature-flag enforcement, instrument/live-intent conversion, live payload shaping, history-root resolution, and the retained live error mapper helper.
- `src/api/_services/metadata_service.py`
  - `health()` and `capabilities()`.
- `src/api/_services/settings_service.py`
  - `get_system_settings()`.
- `src/api/_services/market_data_service.py`
  - `preview_historical_data()`.
- `src/api/_services/research_service.py`
  - `run_strategy()`, `run_ml()`, `run_hybrid()`, and research request/domain mapping helpers.
- `src/api/_services/history_service.py`
  - saved-run summary/detail access, history listing/read, and compare orchestration.
- `src/api/_services/paper_service.py`
  - paper state, orders, cancel, price updates, signal intents, and reset handling.
- `src/api/_services/live_service.py`
  - live status, readiness, intent validation, deprecated compatibility submit rejection, guarded manual submit, and attempt listing.

## Public APIs That Remained Unchanged

- All existing HTTP routes and request/response contracts.
- `api.services.APIService`.
- `api.dependencies.get_api_service()`.
- Feature-flag guard codes/messages.
- Live-execution boundaries and deprecated `/live-execution/intents/submit` behavior.
- Filesystem-backed research history, paper trading state, and live attempt-log behavior.

## Temporary Compatibility Shims

- `src/api/services.py` remains in place as a thin facade so existing imports of `APIService` do not break.
- No new route- or dependency-level compatibility wrappers were introduced.

## Risks And Follow-Up Issues Found

- The facade is now thin, but API-layer schema/domain mapping is still hand-written and repetitive in some domains. That is safer for this phase, but it remains a future cleanup opportunity.
- `common.py` still carries the live error mapping helper for compatibility with the previous service layout even though current live paths do not actively use it.
- History/detail/compare payload shaping still depends on existing persisted artifact structures by design; this refactor intentionally did not normalize or migrate those contracts.

## Validation Results

All required checks passed after the refactor.

- `py -3 -m compileall src/api`
- `py -3 -m unittest tests.api.test_core_flow_regression tests.api.test_research_endpoints tests.api.test_results_detail_endpoint tests.api.test_history_endpoints tests.api.test_compare_endpoints tests.api.test_paper_trading_endpoints tests.api.test_live_execution_endpoints tests.api.test_live_execution_manual_submit tests.api.test_settings_endpoints tests.api.test_health_metadata tests.api.test_safety_defaults_regression`
- `py -3 -m unittest discover tests`
- `py -3 scripts/smoke_check.py` against a locally started backend process
- `npm --prefix frontend run build`

Observed result:

- focused API regression suite passed
- full backend suite passed
- smoke checks passed
- frontend typecheck/build passed
