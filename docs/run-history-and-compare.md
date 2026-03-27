# Run History + Compare Foundation

## Purpose
This phase adds a local-file run history and compare foundation on top of persisted research artifacts.
Runs are now indexed with a manifest and a root index for fast listing/filtering and stable API consumption.

## Storage Layout
- Root: `artifacts/research_runs/`
- Per run:
  - `summary.json`
  - `detail.json`
  - `manifest.json`
- Root index:
  - `index.json`

`ResearchRunner` now updates `manifest.json` and `index.json` whenever a run is persisted.

## Backend APIs
New endpoints:
- `GET /api/v1/history/runs`
- `GET /api/v1/history/runs/{run_id}`
- `POST /api/v1/compare/runs`

Compatibility endpoints remain:
- `GET /api/v1/research/runs`
- `GET /api/v1/research/runs/{run_id}/summary`
- `GET /api/v1/research/runs/{run_id}/detail`

## Frontend
New pages:
- `/history` for browsing/filtering/selecting runs
- `/compare` for comparing 2-5 selected runs

Legacy `/runs` remains as a transition page with links to the new flows.

## Compare Rules (Current Phase)
- Supports strategy compare and ML compare.
- `auto` mode selects a common compatible branch.
- Mixed incompatible selections return validation errors.
- ML compare requires same task type across selected runs.

## Local Workflow
1. Run strategy/ML workflows with persistence enabled.
2. Open `/history` to browse saved runs.
3. Select 2-5 runs and open `/compare`.
4. Inspect compare cards/table and warnings.

## Notes
- Storage is local-file based and optimized for single-developer workflows.
- Corrupt/missing `index.json` auto-rebuilds from available run directories.
- Advanced tagging/search/history permissions are intentionally deferred.
