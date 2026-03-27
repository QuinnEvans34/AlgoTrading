# Local Development Guide

## Goal
Provide one clean way to run backend, frontend, checks, and smoke demos locally.

Python command note: use `py -3` on Windows and `python3` on macOS/Linux.

## Prerequisites
- Python 3.11+ (`py -3 --version`)
- Node.js 20+ and npm (`node --version`, `npm --version`)

## 1) Clone and install

### Backend
```bash
py -3 -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements-dev.txt
```

Optional ML dependency set:
```bash
py -3 -m pip install -r requirements-optional-ml.txt
```

### Frontend
```bash
npm --prefix frontend install
```

## 2) Environment setup

Copy template env:
- Windows: `copy .env.example .env`
- macOS/Linux: `cp .env.example .env`

Frontend-specific override (optional):
- copy `frontend/.env.example` to `frontend/.env.local`

## 3) Initialize local storage
```bash
py -3 scripts/dev.py bootstrap
```

Creates:
- `artifacts/research_runs`
- `artifacts/paper_trading`
- `artifacts/live_execution`

## 4) Start services

### Backend API
```bash
py -3 scripts/dev.py backend
```

### Frontend app (second terminal)
```bash
py -3 scripts/dev.py frontend
```

## 5) Run checks before demo/commit
```bash
py -3 scripts/dev.py check
```

This runs:
1. `python -m compileall src`
2. `python -m unittest discover tests`
3. `npm --prefix frontend run build`

API operability smoke checks:
```bash
py -3 scripts/dev.py smoke
```

## 6) Quick smoke demo
```bash
py -3 scripts/dev.py demo
```

## Troubleshooting

### `ModuleNotFoundError` for backend libs
Re-activate virtual environment and reinstall:
```bash
.venv\Scripts\activate
py -3 -m pip install -r requirements-dev.txt
```

### Frontend cannot reach API
- Ensure backend is running at `http://127.0.0.1:8000`.
- Verify `VITE_API_BASE_URL` in `.env` or `frontend/.env.local`.
- Verify `API_CORS_ALLOWED_ORIGINS` includes frontend origin.

### OANDA/provider calls fail
Expected when credentials are not configured.  
Use inline/synthetic data and local demos for credential-free workflows.

### Live execution submit rejected
Expected by design: live execution is disabled by default and fail-closed.

## Legacy command compatibility
Existing direct script entrypoints remain valid:
- `py -3 scripts/dev_backend.py`
- `py -3 scripts/dev_frontend.py`
- `py -3 scripts/check.py`
- `py -3 scripts/demo_local.py`
