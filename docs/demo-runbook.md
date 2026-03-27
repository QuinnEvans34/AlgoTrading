# Demo Runbook (Local, No Real Credentials)

## Purpose
Repeatable demo flow for reviewers/instructors that proves platform startup, API/UI wiring, checks, and key subsystem behavior without live trading or real broker keys.

Python command note: use `py -3` on Windows and `python3` on macOS/Linux.

## A) One-time setup
```bash
py -3 -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
py -3 -m pip install -r requirements-dev.txt
npm --prefix frontend install
# Windows: copy .env.example .env
# macOS/Linux: cp .env.example .env
py -3 scripts/dev.py bootstrap
```

## B) Quality gate check
```bash
py -3 scripts/dev.py check
```

## C) Start backend and frontend

Terminal 1:
```bash
py -3 scripts/dev.py backend
```

Terminal 2:
```bash
py -3 scripts/dev.py frontend
```

## D) API sanity checks

Health:
```bash
curl http://127.0.0.1:8000/api/v1/health
```

Capabilities:
```bash
curl http://127.0.0.1:8000/api/v1/metadata/capabilities
```

Safe settings snapshot:
```bash
curl http://127.0.0.1:8000/api/v1/settings/system
```

## E) UI workflow checks
1. Open `http://127.0.0.1:5173`
2. Home page: health call returns success.
3. Strategy Run page: submit inline-candle run and confirm summary output.
4. ML Run page: submit inline-candle run and confirm summary output.
5. Paper Trading page: place a market order and confirm state/fills update.
6. Live Execution page: validate intent, attempt manual submit, and confirm guarded rejection by default.
7. Settings page: verify feature flags and live safety status are visible with no secrets.

## F) Scripted smoke demo (optional)
```bash
py -3 scripts/dev.py demo
```

This runs:
- research runner demo
- paper trading demo
- live execution boundary demo
- manual live execution demo

## Expected safety behavior
- Live execution remains disabled by default.
- No real credentials are required for local demo.
- Missing optional provider credentials should degrade cleanly.
