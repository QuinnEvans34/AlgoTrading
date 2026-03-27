# Final Hardening Checklist

Use this checklist before final demos or handoff.

## 1) Environment + startup
- Copy `.env.example` to `.env` (placeholder values only).
- Run bootstrap:
```bash
py -3 scripts/dev.py bootstrap
```
- Start backend and frontend:
```bash
py -3 scripts/dev.py backend
py -3 scripts/dev.py frontend
```

## 2) Automated verification
- Run full quality gate:
```bash
py -3 scripts/dev.py check
```
- Run API operability smoke checks with backend running:
```bash
py -3 scripts/dev.py smoke
```

## 3) Core flow verification
- Strategy research run from UI (`/strategy`) returns a summary.
- ML research run from UI (`/ml`) returns a summary.
- Run history (`/history`) lists saved runs.
- Reopen run detail pages (`/runs/:runId/strategy` and `/runs/:runId/ml`).
- Compare compatible runs from `/history` -> `/compare`.

## 4) Paper + live safety verification
- Paper trading page (`/paper`) supports manual order and state updates.
- Live execution page (`/live-execution`) shows guarded/disabled state by default.
- Settings page (`/settings`) shows runtime flags/status with no secrets exposed.

## 5) Source-of-truth hygiene
- Frontend source-of-truth is TypeScript only (`.ts/.tsx`).
- Generated frontend JS artifacts are not tracked in `frontend/src`.
- Live execution remains disabled by default in config/docs.

## Expected baseline
- All automated checks pass.
- Core research/history/paper flows work.
- Live path stays fail-closed unless explicitly configured.
