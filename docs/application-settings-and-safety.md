# Application Settings / Configuration / Safety Controls

## Purpose
This phase centralizes runtime configuration and safety controls into one backend settings model and exposes a safe read-only runtime snapshot for API/frontend visibility.

## Local Usage
- Copy `.env.example` to `.env` for local configuration defaults.
- Run bootstrap with `py -3 scripts/dev.py bootstrap`.
- Start backend with `py -3 scripts/dev.py backend`.
- Inspect safe runtime snapshot via `GET /api/v1/settings/system` or the frontend `/settings` page.
- Run operability checks with `py -3 scripts/dev.py smoke`.
- Use `docs/final-hardening-checklist.md` for pre-demo verification.

## Backend Settings Model
- `src/config/app_settings.py`: root `AppSettings` with sectioned settings:
  - API server settings
  - storage paths
  - paper trading defaults
  - live safety settings
  - provider settings
  - feature flags
- `src/config/environment.py`: typed env parsing helpers.
- `src/config/feature_flags.py`: feature-flag contract and defaults.
- `src/config/safety.py`: safe serialization (no secret values) for runtime status responses.

## API Exposure
- `GET /api/v1/settings/system`
- Returns safe runtime status with:
  - app/runtime metadata
  - feature flags
  - storage paths
  - paper defaults
  - live safety guardrail status
  - provider readiness booleans
- Never returns raw credential values.

## Feature Flags (v1)
- `FEATURE_RESEARCH_API_ENABLED` (default `true`)
- `FEATURE_HISTORY_API_ENABLED` (default `true`)
- `FEATURE_COMPARE_API_ENABLED` (default `true`)
- `FEATURE_PAPER_TRADING_ENABLED` (default `true`)
- `FEATURE_LIVE_EXECUTION_STATUS_ENABLED` (default `true`)
- `FEATURE_LIVE_EXECUTION_SUBMIT_ENABLED` (default `false`)

## Live Safety Guardrails
- `LIVE_EXECUTION_ENABLED` defaults to `false`.
- `LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION` defaults to `false`.
- `LIVE_EXECUTION_CONFIRMATION_PHRASE` controls required manual submit confirmation text.
- `LIVE_EXECUTION_ATTEMPT_LOG_PATH` controls local guarded-attempt log location.
- Submission remains effectively off unless both the live safety flags and submit feature flag are enabled.

## Frontend Visibility
- New `/settings` page reads `/settings/system`.
- UI panels show runtime, flags, storage paths, paper defaults, and live safety status.
- UI is read-only and does not support secret editing.
