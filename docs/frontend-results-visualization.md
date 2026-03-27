# Frontend Result Visualization Layer

## Purpose
This phase adds route-based result detail pages that visualize persisted research run outputs.
The UI stays thin: all analytics are produced in backend subsystems and rendered here as charts/tables/cards.

## New Result Routes
- `/runs/:runId/strategy`
- `/runs/:runId/ml`

Both routes call:
- `GET /api/v1/research/runs/{run_id}/detail`

## Backend Contract Added
`RunDetailResponse` now includes:
- `summary` (existing run summary payload)
- `strategy_detail` (optional)
- `ml_detail` (optional)

When a run is persisted (`persist_summary=true`), backend now writes:
- `summary.json`
- `detail.json`

under `artifacts/research_runs/<run_id>/`.

Older summary-only runs still load, with `strategy_detail`/`ml_detail` returned as `null`.

## UI Components Added
- KPI cards and metric grid
- Equity curve chart
- Drawdown chart
- Trade ledger table
- Model comparison + split metrics table
- Feature importance panel
- Collapsible raw JSON debug panel

## Local Workflow
1. Start backend:
```bash
py -3 -m uvicorn api.app:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```
2. Start frontend:
```bash
cd frontend
npm install
npm run dev
```
3. Run strategy or ML workflow from `/strategy` or `/ml` with persistence enabled.
4. Open `/runs` and navigate to detail page links.

## Notes
- Charts are lightweight SVG components (no additional chart library dependency).
- Detail pages handle missing optional fields with explicit empty-state messaging.
- This phase does not add run comparison or advanced chart interactions.
