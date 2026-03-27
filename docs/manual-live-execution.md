# Manual Live Execution (Strictly Guarded)

## Purpose
This phase provides a manual-only live execution path behind broker-agnostic contracts, with fail-closed guardrails.

## Safety Defaults
- `LIVE_EXECUTION_ENABLED=false`
- `LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION=false`
- `FEATURE_LIVE_EXECUTION_SUBMIT_ENABLED=false`
- default broker: `null`

No request is submitted unless all guards pass.

## Guard Chain
Manual live orders are checked in this order:
1. submit feature flag enabled
2. live execution enabled
3. live submission enabled
4. broker configured
5. broker adapter supports submit
6. manual confirmation flag set
7. confirmation phrase matches exactly
8. idempotency key is unique
9. intent passes broker capability validation

## API Endpoints
- `GET /api/v1/live-execution/status`
- `GET /api/v1/live-execution/readiness`
- `POST /api/v1/live-execution/intents/validate`
- `POST /api/v1/live-execution/manual-orders`
- `GET /api/v1/live-execution/attempts?limit=25`

Compatibility endpoint:
- `POST /api/v1/live-execution/intents/submit` returns guarded rejection and requires migration to `/manual-orders`.

## Manual Request Contract
`POST /manual-orders` body:
- `intent` (instrument, side, order_type, quantity, optional limit/client order id)
- `idempotency_key`
- `confirm_live_execution` (must be `true`)
- `confirmation_text` (must match configured phrase)
- optional `operator_id`, `operator_note`

## Attempt Logging
- Local log path: `LIVE_EXECUTION_ATTEMPT_LOG_PATH`
- Default: `artifacts/live_execution/attempts.jsonl`
- Stores safe request summary, guard outcomes, acceptance/rejection info.
- No secrets are persisted.

## Frontend
- New operator page: `/live-execution`
- Shows readiness, guard checks, manual submit form, and recent attempts.
- Existing `/broker-status` route redirects to `/live-execution`.

## Notes
- This is not automated trading.
- No strategy-to-live bridge is included in this phase.
- Real broker order placement remains adapter-dependent and may still be blocked by capability.
