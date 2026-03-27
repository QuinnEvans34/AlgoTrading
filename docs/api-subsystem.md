# API Subsystem (Backend Interface Layer)

## Purpose
The API layer exposes current research-platform capabilities over HTTP without moving business logic into route handlers.
Routes validate requests, call the orchestration/service layer, and return structured JSON responses.

## Local Startup (Recommended)
Use repo wrapper scripts for predictable local behavior:

```bash
py -3 scripts/dev.py backend
```

Run full repo checks before demos:

```bash
py -3 scripts/dev.py check
```

Run API operability smoke checks with backend running:

```bash
py -3 scripts/dev.py smoke
```

## Architecture
- `src/api/app.py`: FastAPI app factory and router registration.
- `src/api/routes/*`: thin route modules (`health`, `metadata`, `market_data`, `research`, `results`, `history`, `compare`, `paper_trading`, `live_execution`, `settings`).
- `src/api/schemas.py`: Pydantic request/response contracts.
- `src/api/live_execution_schemas.py`: Pydantic contracts for live boundary endpoints.
- `src/api/settings_schemas.py`: safe runtime settings/status contracts.
- `src/api/services.py`: mapping from API payloads to existing domain contracts and orchestration calls.
- `src/api/serializers.py`: domain artifact -> API response transforms.
- `src/api/errors.py`: standardized error envelope and exception handlers.
- `src/api/dependencies.py`: dependency wiring (`APISettings`, provider registry, market data service, research runner).
- `src/config/*`: centralized app settings and safety snapshot model.

## Endpoints (v1)
- `GET /api/v1/health`
- `GET /api/v1/metadata/capabilities`
- `POST /api/v1/market-data/historical-preview`
- `POST /api/v1/research/strategy-runs`
- `POST /api/v1/research/ml-runs`
- `POST /api/v1/research/hybrid-runs`
- `GET /api/v1/history/runs`
- `GET /api/v1/history/runs/{run_id}`
- `POST /api/v1/compare/runs`
- `GET /api/v1/research/runs`
- `GET /api/v1/research/runs/{run_id}/summary`
- `GET /api/v1/research/runs/{run_id}/detail`
- `GET /api/v1/paper/state`
- `POST /api/v1/paper/orders`
- `POST /api/v1/paper/orders/{order_id}/cancel`
- `POST /api/v1/paper/prices`
- `POST /api/v1/paper/signals`
- `POST /api/v1/paper/reset`
- `GET /api/v1/live-execution/status`
- `GET /api/v1/live-execution/readiness`
- `POST /api/v1/live-execution/intents/validate`
- `POST /api/v1/live-execution/manual-orders`
- `GET /api/v1/live-execution/attempts`
- `POST /api/v1/live-execution/intents/submit` (deprecated compatibility rejection)
- `GET /api/v1/settings/system`

## Error Shape
All API and validation errors use:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request payload validation failed",
    "details": {},
    "request_id": null
  }
}
```

## Environment Variables
- `API_APP_NAME` (default: `capstone-research-api`)
- `API_PREFIX` (default: `/api/v1`)
- `API_HOST` (default: `127.0.0.1`)
- `API_PORT` (default: `8000`)
- `API_DEFAULT_STRICT_FAILURES` (default: `true`)
- `API_DEFAULT_PERSIST_SUMMARY` (default: `false`)
- `API_DEFAULT_RUN_OUTPUT_DIR` (default: `artifacts/research_runs`)
- `API_DEFAULT_PAPER_TRADING_DIR` (default: `artifacts/paper_trading`)
- `API_PAPER_DEFAULT_ACCOUNT_ID` (default: `paper-main`)
- `API_PAPER_DEFAULT_BASE_CURRENCY` (default: `USD`)
- `API_PAPER_DEFAULT_INITIAL_CASH` (default: `100000`)
- `API_PAPER_DEFAULT_ALLOW_SHORT` (default: `false`)
- `API_PAPER_DEFAULT_SPREAD_BPS` (default: `0`)
- `API_PAPER_DEFAULT_SLIPPAGE_BPS` (default: `0`)
- `API_PAPER_DEFAULT_COMMISSION_BPS` (default: `0`)
- `API_PAPER_DEFAULT_COMMISSION_FIXED` (default: `0`)
- `LIVE_EXECUTION_ENABLED` (default: `false`)
- `LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION` (default: `false`)
- `LIVE_EXECUTION_BROKER` (default: `null`)
- `LIVE_EXECUTION_REQUEST_TIMEOUT_SECONDS` (default: `10`)
- `LIVE_EXECUTION_CONFIRMATION_PHRASE` (default: `EXECUTE LIVE ORDER`)
- `LIVE_EXECUTION_ATTEMPT_LOG_PATH` (default: `artifacts/live_execution/attempts.jsonl`)
- `LIVE_OANDA_API_TOKEN` (placeholder, optional)
- `LIVE_OANDA_ACCOUNT_ID` (placeholder, optional)
- `LIVE_OANDA_ENVIRONMENT` (default: `practice`)
- `FEATURE_RESEARCH_API_ENABLED` (default: `true`)
- `FEATURE_HISTORY_API_ENABLED` (default: `true`)
- `FEATURE_COMPARE_API_ENABLED` (default: `true`)
- `FEATURE_PAPER_TRADING_ENABLED` (default: `true`)
- `FEATURE_LIVE_EXECUTION_STATUS_ENABLED` (default: `true`)
- `FEATURE_LIVE_EXECUTION_SUBMIT_ENABLED` (default: `false`)
- `API_CORS_ALLOWED_ORIGINS` (CSV, default includes `http://localhost:5173,http://127.0.0.1:5173`)

Optional OANDA provider registration:
- `API_ENABLE_OANDA_PROVIDER` (default: `false`)
- `OANDA_API_TOKEN`
- `OANDA_ACCOUNT_ID` (optional for quote preview, required for live quote paths)
- `OANDA_ENVIRONMENT` (`practice` or `live`)
- `OANDA_TIMEOUT_SECONDS` (default: `15`)

## Notes
- This phase is synchronous: long research runs block request completion.
- Persisted run retrieval uses local artifacts + manifest/index (`summary.json`, `detail.json`, `manifest.json`, `index.json`).
- Paper trading state uses local persistence at `artifacts/paper_trading/state.json` by default.
- Live execution boundary is fail-closed by default and uses placeholder adapters only in this phase.
- `/settings/system` returns safe runtime status and never includes raw secret values.
- Provider registration is optional; metadata may show zero providers if none are configured.
- `/live-execution/intents/submit` remains a deprecated compatibility route and does not provide a direct live path.
