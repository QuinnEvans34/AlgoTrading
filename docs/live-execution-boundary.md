# Live Execution Boundary (Broker Adapter Interfaces)

## Purpose
This subsystem defines a strict, broker-agnostic seam for future live execution.
It is disabled by default and does not place real orders in this phase.

## Scope in This Phase
- Broker interface contracts for future adapters.
- Capability model for asset/order support checks.
- Readiness snapshot and ordered guard-chain evaluation.
- Manual live order submission contract with explicit confirmation + idempotency.
- Guarded submit path that fails closed unless explicitly enabled/configured and manually confirmed.
- Local live-attempt logging for operational visibility.
- Null adapter default plus an OANDA stub placeholder.

## Package Layout
- `src/live_execution/contracts.py`: core enums and dataclasses for intents, capabilities, status, and snapshots.
- `src/live_execution/config.py`: live boundary settings contract.
- `src/live_execution/exceptions.py`: explicit guardrail and adapter errors.
- `src/live_execution/validation.py`: intent normalization and capability checks.
- `src/live_execution/service.py`: status, validation, and guarded submit orchestration.
- `src/live_execution/brokers/base.py`: adapter interface.
- `src/live_execution/brokers/null_broker.py`: fail-closed default.
- `src/live_execution/brokers/oanda_stub.py`: placeholder-only mapping skeleton.
- `src/live_execution/brokers/registry.py`: adapter selection.

## Safety Guardrails
- `LIVE_EXECUTION_ENABLED=false` by default.
- `LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION=false` by default.
- Default broker is `null` (non-configured, non-submitting).
- Submit attempts return explicit rejection errors unless all guardrails are enabled.
- OANDA adapter in this phase is a stub only and does not execute real HTTP orders.

## API Surface
- `GET /api/v1/live-execution/status`
- `GET /api/v1/live-execution/readiness`
- `POST /api/v1/live-execution/intents/validate`
- `POST /api/v1/live-execution/manual-orders`
- `GET /api/v1/live-execution/attempts`
- `POST /api/v1/live-execution/intents/submit` (deprecated compatibility rejection)

Manual order endpoint is the only submission path in this phase.

## Environment Variables
- `LIVE_EXECUTION_ENABLED` (default `false`)
- `LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION` (default `false`)
- `LIVE_EXECUTION_BROKER` (`null` or `oanda_stub`, default `null`)
- `LIVE_EXECUTION_REQUEST_TIMEOUT_SECONDS` (default `10`)
- `LIVE_EXECUTION_CONFIRMATION_PHRASE` (default `EXECUTE LIVE ORDER`)
- `LIVE_EXECUTION_ATTEMPT_LOG_PATH` (default `artifacts/live_execution/attempts.jsonl`)
- `LIVE_OANDA_API_TOKEN` (placeholder)
- `LIVE_OANDA_ACCOUNT_ID` (placeholder)
- `LIVE_OANDA_ENVIRONMENT` (default `practice`)

## Notes
- This boundary is intentionally separate from paper trading and backtesting.
- Capability model will expand when real broker adapters are implemented.
- Full live order lifecycle/reconciliation are deferred.
