# Capstone Research Platform

Backend-first multi-asset research platform with:
- market data adapters
- strategy and backtesting flows
- diagnostics and ML research
- run history and compare
- paper-trading sandbox
- disabled-by-default live-execution boundary
- React app shell

Python command note: use `py -3` on Windows and `python3` on macOS/Linux.

## Quickstart

1. Backend setup:
```bash
py -3 -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements-dev.txt
```

2. Frontend setup:
```bash
npm --prefix frontend install
```

3. Local env and bootstrap:
```bash
# Windows: copy .env.example .env
# macOS/Linux: cp .env.example .env
py -3 scripts/dev.py bootstrap
```
By default this now also starts a local Postgres container and runs `alembic upgrade head` when `DATABASE_ENABLED=true` and `DATABASE_URL` is set.

4. Start backend/frontend:
```bash
py -3 scripts/dev.py backend
```
Second terminal:
```bash
py -3 scripts/dev.py frontend
```

5. Run checks and smoke validation:
```bash
py -3 scripts/dev.py check
py -3 scripts/dev.py smoke
```

6. Run local demo flow:
```bash
py -3 scripts/dev.py demo
```

## Canonical Dev Commands

- Bootstrap preflight: `py -3 scripts/dev.py bootstrap`
- Legacy metadata backfill: `py -3 scripts/backfill_research_metadata.py`
- Metadata transition report: `py -3 scripts/backfill_research_metadata.py --report-only`
- Backend dev server: `py -3 scripts/dev.py backend`
- Frontend dev server: `py -3 scripts/dev.py frontend`
- Full checks: `py -3 scripts/dev.py check`
- API smoke checks: `py -3 scripts/dev.py smoke`
- Deterministic demo: `py -3 scripts/dev.py demo`

Legacy script entrypoints (`scripts/dev_backend.py`, etc.) remain supported for compatibility.

## Documentation

- Local development guide: `docs/local-development.md`
- Persistence foundation phase B1: `docs/persistence-foundation-phase-b1.md`
- Persistence transition hardening phase B2: `docs/persistence-transition-hardening-phase-b2.md`
- Workflow persistence phase B3: `docs/workflow-persistence-phase-b3.md`
- Demo runbook: `docs/demo-runbook.md`
- Deployment/dev foundation: `docs/deployment-foundation.md`
- Final hardening checklist: `docs/final-hardening-checklist.md`
- API subsystem: `docs/api-subsystem.md`
- Frontend shell: `docs/frontend-app-shell.md`
- Settings and safety: `docs/application-settings-and-safety.md`
- Manual live execution: `docs/manual-live-execution.md`

## Notes

- Defaults are demo-safe (live execution disabled, no real credentials required).
- Optional provider credentials can remain blank for local development.
- Frontend source of truth is TypeScript (`.ts/.tsx`).
