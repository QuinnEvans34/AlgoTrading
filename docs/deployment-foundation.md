# Deployment / Dev-Experience / Operations Foundation

## Purpose
This layer standardizes how developers/operators run, validate, and demo the full stack locally without adding heavy infrastructure.

Python command note: use `py -3` on Windows and `python3` on macOS/Linux.

## Canonical Task Runner
Use `scripts/dev.py` as the default command entrypoint:

- `py -3 scripts/dev.py bootstrap`
- `py -3 scripts/dev.py backend`
- `py -3 scripts/dev.py frontend`
- `py -3 scripts/dev.py check`
- `py -3 scripts/dev.py smoke`
- `py -3 scripts/dev.py demo`

Legacy direct scripts remain available for compatibility.

## Startup Model
1. `bootstrap` loads `.env`, validates local prerequisites, and initializes artifact directories.
2. `backend` starts FastAPI via uvicorn with safe defaults from env/settings.
3. `frontend` starts Vite using configured API base URL.
4. `smoke` validates key runtime endpoints:
   - `/api/v1/health`
   - `/api/v1/metadata/capabilities`
   - `/api/v1/settings/system`
   - `/api/v1/live-execution/readiness`

## Safe Defaults
- Live execution remains disabled by default.
- No real provider/broker credentials are required for local demo workflows.
- Env templates include placeholders only; no secrets are committed.

## Environment Files
- Root runtime template: `.env.example`
- Frontend local override template: `frontend/.env.example`
- Optional credential documentation: `docs/credentials/*`

## What This Phase Does Not Add
- Cloud deployment pipelines.
- Kubernetes/Terraform.
- CI/CD automation.
- Docker/devcontainer orchestration.

These are intentionally deferred until local workflows and hosting targets are stable.
