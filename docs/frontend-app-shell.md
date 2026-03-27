# Frontend App Shell (React + API Integration)

## Purpose
This frontend phase adds a functional React shell that calls the existing backend API.
The UI is intentionally thin: forms capture workflow inputs, backend performs orchestration/validation, and the app renders structured run summaries.

## Stack
- React + TypeScript
- Vite
- React Router
- Fetch-based API client with typed request/response contracts

## File Structure
- `frontend/src/pages`: page-level workflows (`Home`, `Metadata`, `Settings`, `Strategy`, `ML`, `Paper`, `History`, `Compare`, `LiveExecution`, `Runs`)
- `frontend/src/components/forms`: workflow input forms and candle-source fields
- `frontend/src/components/results`: run summary and step timeline rendering
- `frontend/src/components/settings`: runtime settings/status visibility panels
- `frontend/src/lib/api`: typed API client and endpoint modules
- `frontend/src/lib/liveExecution`: typed client/contracts for live readiness, manual submit, and attempt visibility
- `frontend/src/lib/settings`: typed client/contracts for system settings endpoint
- `frontend/src/lib/config.ts`: API base URL config

## Backend Compatibility
Backend API now supports CORS origins from config:
- `API_CORS_ALLOWED_ORIGINS` (CSV list)
- Defaults include:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`

## Local Development
Install frontend dependencies once:
```bash
npm --prefix frontend install
```

### 1) Start backend API (recommended wrapper)
```bash
py -3 scripts/dev.py backend
```

### 2) Start frontend app (recommended wrapper)
```bash
py -3 scripts/dev.py frontend
```

### 3) Optional API base URL override
Create `frontend/.env.local`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### 4) Run quality checks
```bash
py -3 scripts/dev.py check
```

## Current User Flows
- Home: health check (`GET /health`)
- Metadata: capabilities (`GET /metadata/capabilities`)
- Strategy Run: submit form to `POST /research/strategy-runs`
- ML Run: submit form to `POST /research/ml-runs`
- Runs: list/get persisted run summaries (`GET /research/runs`, `GET /research/runs/{run_id}/summary`)
- Paper Trading: sandbox account operations (`GET /paper/state`, `POST /paper/orders`, `POST /paper/prices`, `POST /paper/orders/{order_id}/cancel`, `POST /paper/reset`)
- Live Execution: guarded manual live flow (`GET /live-execution/readiness`, `POST /live-execution/manual-orders`, `GET /live-execution/attempts`, `POST /live-execution/intents/validate`)
- Settings: safe runtime visibility (`GET /settings/system`)

## Notes
- Inline sample candles are the default source so the shell works without provider/API keys.
- Market-data fetch mode is available but depends on backend provider registration (e.g., OANDA env setup).
- Result rendering is summary-first; charting and advanced diagnostics visuals are intentionally deferred.
- Live execution remains disabled by default; manual submit requires explicit guard confirmation and is expected to reject unless all safety controls pass.
- Settings page is read-only and does not expose credential values.
- TypeScript (`.ts/.tsx`) is the frontend source-of-truth. Generated JS artifacts under `frontend/src` are intentionally not tracked.
